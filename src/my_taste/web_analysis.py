from __future__ import annotations

import ipaddress
import socket
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .media_analysis import analyze_image_file


def _validate_public_http_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("website URL must use http or https")
    if not parsed.hostname:
        raise ValueError("website URL must include a hostname")

    host = parsed.hostname
    try:
        addresses = {row[4][0] for row in socket.getaddrinfo(host, parsed.port or 443)}
    except socket.gaierror as exc:
        raise ValueError(f"could not resolve website hostname: {host}") from exc

    for value in addresses:
        ip = ipaddress.ip_address(value)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ValueError("website URL resolves to a non-public network address")

    return url


_CAPTURE_JS = r"""
(limit) => {
  const compact = (value) => {
    if (value === null || value === undefined) return null;
    const text = String(value);
    return text.length > 240 ? text.slice(0, 240) : text;
  };

  const selectors = [
    "header", "nav", "main", "section", "article", "footer",
    "h1", "h2", "h3", "p", "a", "button", "input", "textarea",
    "img", "video", "[role='button']", "[role='dialog']"
  ];

  const seen = new Set();
  const nodes = [];
  for (const selector of selectors) {
    for (const el of document.querySelectorAll(selector)) {
      if (seen.has(el) || nodes.length >= limit) continue;
      const rect = el.getBoundingClientRect();
      if (rect.width < 2 || rect.height < 2) continue;
      if (rect.bottom < -window.innerHeight || rect.top > window.innerHeight * 4) continue;
      seen.add(el);
      nodes.push(el);
    }
  }

  const vw = window.innerWidth || 1;
  const vh = window.innerHeight || 1;

  const elements = nodes.map((el, index) => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return {
      index,
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute("role"),
      text: compact((el.innerText || el.getAttribute("aria-label") || "").trim()),
      geometry: {
        x_px: Math.round(rect.x * 100) / 100,
        y_px: Math.round(rect.y * 100) / 100,
        width_px: Math.round(rect.width * 100) / 100,
        height_px: Math.round(rect.height * 100) / 100,
        x_vw: Math.round((rect.x / vw) * 10000) / 10000,
        y_vh: Math.round((rect.y / vh) * 10000) / 10000,
        width_vw: Math.round((rect.width / vw) * 10000) / 10000,
        height_vh: Math.round((rect.height / vh) * 10000) / 10000
      },
      style: {
        display: style.display,
        position: style.position,
        fontFamily: compact(style.fontFamily),
        fontSize: style.fontSize,
        fontWeight: style.fontWeight,
        lineHeight: style.lineHeight,
        letterSpacing: style.letterSpacing,
        color: style.color,
        backgroundColor: style.backgroundColor,
        border: compact(style.border),
        borderRadius: style.borderRadius,
        boxShadow: compact(style.boxShadow),
        opacity: style.opacity,
        gap: style.gap,
        padding: style.padding,
        margin: style.margin,
        transform: compact(style.transform),
        filter: compact(style.filter),
        transitionProperty: compact(style.transitionProperty),
        transitionDuration: compact(style.transitionDuration),
        transitionTimingFunction: compact(style.transitionTimingFunction),
        transitionDelay: compact(style.transitionDelay)
      }
    };
  });

  const animations = document.getAnimations().slice(0, 100).map((animation, index) => {
    const effect = animation.effect;
    const timing = effect && effect.getTiming ? effect.getTiming() : {};
    const target = effect && effect.target;
    let keyframes = [];
    try {
      keyframes = effect && effect.getKeyframes ? effect.getKeyframes().slice(0, 20) : [];
    } catch (_) {}
    return {
      index,
      playState: animation.playState,
      currentTime_ms: typeof animation.currentTime === "number" ? animation.currentTime : null,
      target: target ? {
        tag: target.tagName ? target.tagName.toLowerCase() : null,
        id: target.id || null,
        className: compact(target.className || "")
      } : null,
      timing: {
        delay_ms: timing.delay ?? null,
        duration_ms: timing.duration ?? null,
        easing: timing.easing ?? null,
        iterations: timing.iterations ?? null,
        direction: timing.direction ?? null,
        fill: timing.fill ?? null
      },
      keyframes: keyframes.map(frame => {
        const copy = {};
        for (const [key, value] of Object.entries(frame)) {
          if (["computedOffset", "easing", "offset", "composite"].includes(key) ||
              ["opacity", "transform", "filter", "color", "backgroundColor", "clipPath"].includes(key)) {
            copy[key] = compact(value);
          }
        }
        return copy;
      })
    };
  });

  const rootStyle = getComputedStyle(document.documentElement);
  const cssVariables = {};
  for (const name of Array.from(rootStyle)) {
    if (!name.startsWith("--")) continue;
    const value = rootStyle.getPropertyValue(name).trim();
    if (value && Object.keys(cssVariables).length < 120) cssVariables[name] = compact(value);
  }

  const mediaQueries = [];
  for (const sheet of Array.from(document.styleSheets)) {
    let rules;
    try { rules = sheet.cssRules; } catch (_) { continue; }
    for (const rule of Array.from(rules || [])) {
      if (rule.media && rule.media.mediaText && mediaQueries.length < 100) {
        mediaQueries.push(rule.media.mediaText);
      }
    }
  }

  const fonts = [];
  try {
    for (const face of Array.from(document.fonts || [])) {
      if (fonts.length >= 50) break;
      fonts.push({
        family: face.family,
        style: face.style,
        weight: face.weight,
        status: face.status
      });
    }
  } catch (_) {}

  return {
    url: location.href,
    title: document.title,
    viewport: {
      width_px: window.innerWidth,
      height_px: window.innerHeight,
      devicePixelRatio: window.devicePixelRatio,
      scrollY_px: window.scrollY,
      documentHeight_px: Math.max(
        document.documentElement.scrollHeight,
        document.body ? document.body.scrollHeight : 0
      )
    },
    cssVariables,
    mediaQueries: Array.from(new Set(mediaQueries)),
    fonts,
    elements,
    animations
  };
}
"""


def analyze_website(
    url: str,
    *,
    width: int = 1440,
    height: int = 1000,
    max_elements: int = 140,
    settle_ms: int = 700,
) -> dict[str, Any]:
    """Forensically inspect a public live website with installed Chrome.

    Returns rendered pixel evidence, computed styles/geometry, responsive hints,
    and Web Animations API observations from load and scroll states.
    """
    _validate_public_http_url(url)
    width = max(320, min(int(width), 2560))
    height = max(480, min(int(height), 1800))
    max_elements = max(20, min(int(max_elements), 250))
    settle_ms = max(100, min(int(settle_ms), 3000))

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("playwright is not installed in the My Taste runtime") from exc

    with sync_playwright() as playwright:
        browser = None
        launch_errors: list[str] = []
        for kwargs in ({"channel": "chrome"}, {}):
            try:
                browser = playwright.chromium.launch(headless=True, **kwargs)
                break
            except Exception as exc:  # browser availability varies by host
                launch_errors.append(str(exc))

        if browser is None:
            raise RuntimeError(
                "Could not launch Chrome/Chromium for deep website capture. "
                + " | ".join(launch_errors[-2:])
            )

        try:
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(min(250, settle_ms))

            initial = page.evaluate(_CAPTURE_JS, max_elements)
            page.wait_for_timeout(settle_ms)

            with tempfile.TemporaryDirectory() as tmp:
                screenshot = Path(tmp) / "page.png"
                page.screenshot(path=str(screenshot), full_page=True)
                pixels = analyze_image_file(screenshot)

            document_height = int(initial["viewport"]["documentHeight_px"])
            if document_height > height:
                page.evaluate(
                    "(y) => window.scrollTo({top: y, behavior: 'instant'})",
                    max(0, document_height // 2),
                )
                page.wait_for_timeout(settle_ms)
                scrolled = page.evaluate(_CAPTURE_JS, max_elements)
            else:
                scrolled = initial

            return {
                "capture": {
                    "kind": "live_dom_css_motion",
                    "fidelity": "dom_css+motion_timeline+rendered_pixels",
                    "motion_observable": True,
                    "interaction_observable": True,
                    "viewport_requested": {"width_px": width, "height_px": height},
                },
                "rendered_pixels": pixels,
                "initial_state": initial,
                "scrolled_state": scrolled,
            }
        finally:
            browser.close()
