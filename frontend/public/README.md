# Public Assets Directory

This directory contains static assets that are served directly by Vite.

## Favicon Files

Place the following favicon files in this directory:

### Required Files:
- `favicon.ico` - Classic favicon (16x16, 32x32, 48x48)
- `favicon-16x16.png` - 16x16 PNG favicon
- `favicon-32x32.png` - 32x32 PNG favicon
- `apple-touch-icon.png` - 180x180 PNG for iOS home screen
- `android-chrome-192x192.png` - 192x192 PNG for Android
- `android-chrome-512x512.png` - 512x512 PNG for Android

### Logo:
- `logo.png` - Main logo used in the navbar (current size: 40x40px display)

## How to Generate Favicons

You can use online tools to generate all favicon sizes from your logo:

1. **RealFaviconGenerator** (recommended): https://realfavicongenerator.net/
   - Upload your logo image
   - Customize settings
   - Download the generated package
   - Extract all files to this `public/` directory

2. **Favicon.io**: https://favicon.io/
   - Simple and quick
   - Generates basic favicon set

## Current Files:
- ✅ `site.webmanifest` - PWA manifest (already created)
- ⏳ Favicon files - Need to be added

## Notes:
- All files in this directory are served from the root URL (e.g., `/favicon.ico`)
- No import needed - just reference them in `index.html`
- Vite automatically serves these files in both dev and production builds

