/**
 * Copyright 2026 The SCOUT Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: 'class',
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "tertiary-fixed-dim": "#ffb695",
        "surface-container-low": "#f3f4f5",
        "surface-bright": "#f8f9fa",
        "on-secondary-fixed": "#140f54",
        "on-secondary-fixed-variant": "#413f82",
        "on-background": "#191c1d",
        "surface-container-lowest": "#ffffff",
        "on-secondary": "#ffffff",
        "primary": "#3525cd",
        "on-error": "#ffffff",
        "on-primary-fixed": "#0f0069",
        "secondary-container": "#b6b4ff",
        "background": "#f8f9fa",
        "surface-dim": "#d9dadb",
        "outline-variant": "#c7c4d8",
        "on-tertiary-fixed-variant": "#7b2f00",
        "on-primary-fixed-variant": "#3323cc",
        "error": "#ba1a1a",
        "error-container": "#ffdad6",
        "surface": "#f8f9fa",
        "tertiary-fixed": "#ffdbcc",
        "tertiary": "#7e3000",
        "surface-container-high": "#e7e8e9",
        "surface-tint": "#4d44e3",
        "primary-fixed": "#e2dfff",
        "surface-variant": "#e1e3e4",
        "inverse-primary": "#c3c0ff",
        "on-primary-container": "#dad7ff",
        "on-surface-variant": "#464555",
        "on-tertiary-fixed": "#351000",
        "surface-container": "#edeeef",
        "surface-container-highest": "#e1e3e4",
        "inverse-on-surface": "#f0f1f2",
        "on-tertiary-container": "#ffd2be",
        "secondary-fixed-dim": "#c3c0ff",
        "on-error-container": "#93000a",
        "secondary-fixed": "#e2dfff",
        "outline": "#777587",
        "on-secondary-container": "#454386",
        "on-primary": "#ffffff",
        "on-surface": "#191c1d",
        "primary-fixed-dim": "#c3c0ff",
        "on-tertiary": "#ffffff",
        "primary-container": "#4f46e5",
        "secondary": "#58579b",
        "tertiary-container": "#a44100",
        "inverse-surface": "#2e3132"
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "lg": "0.5rem",
        "xl": "0.75rem",
        "full": "9999px"
      },
      fontFamily: {
        "headline": ["var(--font-manrope)"],
        "manrope": ["var(--font-manrope)"],   /* FIX: layout.tsx uses className="font-manrope" directly */
        "body": ["var(--font-inter)"],
        "label": ["var(--font-inter)"]
      }
    },
  },
  plugins: [],
};
export default config;
