// ==UserScript==
// @name         Wide Test
// @namespace    test
// @version      1.0
// @description  Fixture for the user script tests.
// @author       Jane Example
// @homepageURL  https://example.org/wide
// @license      MIT
// @match        *://127.0.0.1/*
// @include      https://*.example.org/*
// @exclude      *://127.0.0.1/excluded/*
// @run-at       document-end
// @noframes
// @grant        GM.addStyle
// @grant        GM.notification
// @grant        GM_xmlhttpRequest
// @grant        GM_xmlhttpRequest
// @resource     logo https://example.org/logo.png
// @require      lib.js
// @updateURL    https://example.org/wide.meta.js
// @downloadURL  https://example.org/wide.user.js
// ==/UserScript==

greet("wide");
