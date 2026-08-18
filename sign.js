const fs = require('fs');
const vm = require('vm');

function main() {
  const [url, body, pathsArg] = process.argv.slice(2);
  const u = url || 'https://api.juejin.cn/growth_api/v1/lottery/draw?aid=2608&uuid=7661864643350988324&spider=0';
  const payload = body || '';

  const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36';
  let COOKIE = '';
  try {
    const cookies = JSON.parse(fs.readFileSync(__dirname + '\\cookies.json', 'utf8'));
    const jj = cookies.filter(c => (c.domain || '').indexOf('juejin.cn') >= 0 || (c.domain || '').indexOf('bytedance.com') >= 0);
    COOKIE = jj.map(c => `${c.name}=${c.value}`).join('; ');
  } catch (e) { COOKIE = ''; }
  if (!COOKIE) {
    console.log('SIGN ERROR_NO_COOKIE');
    process.exit(1);
  }

  const noop = () => {};
  const raf = cb => setTimeout(cb, 16);

  const wrapCache = new WeakMap();
  function L(name, obj) {
    const cache = {};
    const cached = wrapCache.get(obj);
    if (cached) return cached;
    const proxy = new Proxy(obj, {
      get(t, p) {
        if (p === Symbol.toPrimitive) return () => obj.toString ? obj.toString() : '';
        if (typeof p === 'symbol') return t[p];
        if (p === 'window' || p === 'self' || p === 'globalThis' || p === 'parent' || p === 'top' || p === 'frames') {
          return t[p] === t ? proxy : Reflect.get(t, p);
        }
        const full = `${name}.${String(p)}`;
        let v = Reflect.get(t, p);
        if (v && typeof v === 'object' && !cache[p]) v = cache[p] = L(full, v);
        else if (typeof v === 'function' && !cache[p]) {
          const orig = v;
          v = cache[p] = function (...a) { return orig.apply(t, a); };
        }
        return v;
      },
      set(t, p, v) { return Reflect.set(t, p, v); },
    });
    wrapCache.set(obj, proxy);
    return proxy;
  }

  let RESULT = null;
  const fetchCapture = (urlx, opts) => {
    const uu = typeof urlx === 'string' ? urlx : (urlx && urlx.href) || String(urlx);
    if (uu.indexOf('a_bogus') >= 0) {
      const i = uu.lastIndexOf('a_bogus=');
      RESULT = { url: uu, bogus: decodeURIComponent(uu.slice(i + 8)) };
    }
    return new Promise(() => {});
  };

  const custom = () => ({ style: {}, dataset: {}, setAttribute: noop, appendChild: noop });
  const sandbox = {
    console, setTimeout, clearTimeout, setInterval, clearInterval, setImmediate, clearImmediate,
    Promise, Date, Math, JSON, Object, Array, String, Error, TypeError, RegExp,
    parseInt, parseFloat, isNaN, isFinite, encodeURIComponent, encodeURI,
    decodeURIComponent, decodeURI, eval,
    WebSocket, Request, Headers, Response,
    fetch: fetchCapture,
    Intl, Symbol, Map, Set, WeakMap, WeakSet, Proxy, Reflect, Uint8Array, Uint8ClampedArray,
    ArrayBuffer, DataView, Float32Array, Float64Array, Int32Array, Uint32Array, Int16Array,
    Uint16Array, BigInt, Number, Boolean, Function, Infinity, NaN, undefined,
    Performance, performance: { now: () => Date.now(), timing: { navigationStart: Date.now() - 10000 } },
    AbortController, TextEncoder, TextDecoder, atob, btoa,
    DOMException: typeof DOMException !== 'undefined' ? DOMException : class DOMException extends Error {},
  };

  const base = {
    document: {
      cookie: COOKIE,
      referrer: 'https://juejin.cn/',
      title: 'juejin',
      URL: 'https://juejin.cn/user/signin?from=default',
      documentElement: { style: {}, dataset: {}, getAttribute: () => null, setAttribute: noop, clientWidth: 1920, clientHeight: 1040, scrollWidth: 1920, scrollHeight: 1040, getBoundingClientRect: () => ({ top: 0, left: 0, width: 1920, height: 1040 }) },
      head: { appendChild: noop }, body: { appendChild: noop },
      createElement: tag => custom(),
      createElementNS: () => ({}),
      createEvent: () => ({ initEvent: noop, initMouseEvent: noop, target: null, type: '' }),
      createTextNode: () => ({ nodeType: 3, textContent: '' }),
      createComment: () => ({ nodeType: 8 }),
      createDocumentFragment: () => ({ appendChild: noop }),
      createAttribute: name => ({ name, value: '' }),
      getElementsByTagName: () => [], getElementsByClassName: () => [], getElementsByName: () => [],
      getElementById: () => null, querySelector: () => null, querySelectorAll: () => [],
      addEventListener: noop, removeEventListener: noop,
      all: [], characterSet: 'UTF-8', compatMode: 'CSS1Compat',
      documentURI: 'https://juejin.cn/', charset: 'UTF-8',
      hidden: false, visibilityState: 'visible', readyState: 'complete', defaultView: null,
      activeElement: null, images: [], scripts: [], links: [], forms: [], anchors: [],
      location: { href: 'https://juejin.cn/', protocol: 'https:', host: 'juejin.cn', hostname: 'juejin.cn', pathname: '/', search: '', hash: '' },
    },
    navigator: {
      userAgent: UA,
      appVersion: '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
      platform: 'Win32', language: 'zh-CN', languages: ['zh-CN', 'zh'],
      vendor: 'Google Inc.', appName: 'Netscape', appCodeName: 'Mozilla',
      product: 'Gecko', productSub: '20030107',
      hardwareConcurrency: 8, deviceMemory: 8, maxTouchPoints: 0,
      onLine: true, cookieEnabled: true, webdriver: false, mimeTypes: [], plugins: [],
      getBattery: () => Promise.resolve({ level: 1, charging: true, chargingTime: 0, dischargingTime: Infinity, addEventListener: noop }),
      userAgentData: {
        brands: [{ brand: 'Not;A=Brand', version: '8' }, { brand: 'Chromium', version: '150' }, { brand: 'Google Chrome', version: '150' }],
        mobile: false, platform: 'Windows',
        getHighEntropyValues: () => Promise.resolve({ architecture: 'x86', bitness: '64', model: '', platformVersion: '17.0', uaFullVersion: '150.0.0.0' }),
      },
    },
    location: { href: 'https://juejin.cn/', protocol: 'https:', host: 'juejin.cn', hostname: 'juejin.cn', pathname: '/', search: '', hash: '', origin: 'https://juejin.cn', port: '', assign: noop, replace: noop, reload: noop, toString: () => 'https://juejin.cn/' },
    history: { length: 1, state: null, back: noop, forward: noop, go: noop, pushState: noop, replaceState: noop },
    Image: function Image() { return { onerror: null, onload: null, src: '' }; },
    PluginArray: function PluginArray() {},
    indexedDB: { open: () => ({ onupgradeneeded: null, onsuccess: null, onerror: null, result: null }), deleteDatabase: () => ({}) },
    safari: {}, InstallTrigger: undefined,
    requestAnimationFrame: raf, cancelAnimationFrame: clearTimeout,
    screen: { width: 1920, height: 1080, availWidth: 1920, availHeight: 1040, colorDepth: 24, pixelDepth: 24, orientation: { type: 'landscape-primary', angle: 0 } },
    devicePixelRatio: 1, visualViewport: { width: 1920, height: 1040, offsetLeft: 0, offsetTop: 0, scale: 1 },
    innerWidth: 1920, innerHeight: 1040, outerWidth: 1920, outerHeight: 1040, screenX: 0, screenY: 0,
    pageXOffset: 0, pageYOffset: 0, scrollX: 0, scrollY: 0, deviceMemory: 8,
    chrome: { loadTimes: () => ({}), csi: () => ({}), app: {} },
    self: null, localStorage: { getItem: () => null, setItem: noop, removeItem: noop, clear: noop, key: () => null, length: 0 },
    XMLHttpRequest: class {
      constructor() { this.readyState = 0; this.status = 0; this.responseText = ''; this.response = ''; this.statusText = ''; this.withCredentials = true; this.onreadystatechange = null; this.onload = null; this.onerror = null; this._headers = {}; this._method = ''; this._url = ''; this.timeout = 0; this.upload = {}; }
      open(m, x) { this._method = m; this._url = x; this.readyState = 1; }
      setRequestHeader(k, v) { this._headers[k.toLowerCase()] = v; }
      send() {}
      getResponseHeader() { return null; }
      getAllResponseHeaders() { return ''; }
      addEventListener() {} removeEventListener() {} abort() {} overrideMimeType() {}
    },
    URL: typeof URL !== 'undefined' ? URL : undefined,
  };

  for (const k of Object.keys(base)) {
    const o = base[k];
    sandbox[k] = (o !== null && typeof o === 'object') ? L(k, o) : o;
  }
  class EventTarget {}
  class Node extends EventTarget {}
  class Element extends Node {}
  class HTMLElement extends Element { style = {}; dataset = {}; addEventListener() {} removeEventListener() {} appendChild() {} setAttribute() {} getAttribute() { return null; } }
  class HTMLCanvasElement extends HTMLElement { getContext() { return { getImageData: () => ({ data: new Uint8ClampedArray(4), width: 1, height: 1 }), fillRect: noop, beginPath: noop, arc: noop, fill: noop, stroke: noop, rect: noop, drawImage: noop, createLinearGradient: () => ({ addColorStop: noop }), measureText: () => ({ width: 0 }) }; } toDataURL() { return 'data:image/png;base64,AAA'; } }
  class HTMLDivElement extends HTMLElement {}
  class HTMLScriptElement extends HTMLElement {}
  class HTMLIFrameElement extends HTMLElement {}
  class Document extends Node { cookie = COOKIE; referrer = 'https://juejin.cn/'; createElement() { return new HTMLDivElement(); } addEventListener() {} removeEventListener() {} querySelector() { return null; } querySelectorAll() { return []; } getElementById() { return null; } }
  class HTMLDocument extends Document {}
  class XMLDocument extends Document {}
  class Event {}
  class CustomEvent extends Event {}
  class MouseEvent extends Event {}
  class KeyboardEvent extends Event {}
  class Screen {}
  class Storage {}
  class CSSStyleDeclaration {}
  class DOMTokenList {}
  class HTMLElementCollection {}
  Object.assign(sandbox, {
    EventTarget, Node, Element, HTMLElement, HTMLCanvasElement, HTMLDivElement,
    HTMLScriptElement, HTMLIFrameElement, Document, HTMLDocument, XMLDocument,
    Event, CustomEvent, MouseEvent, KeyboardEvent, Screen, Storage, CSSStyleDeclaration,
    MutationObserver: class MutationObserver { observe() {} disconnect() {} takeRecords() { return []; } },
    getBattery: undefined,
  });
  sandbox.addEventListener = noop;
  sandbox.removeEventListener = noop;
  sandbox.dispatchEvent = () => true;
  sandbox.getComputedStyle = () => ({ getPropertyValue: () => '', cssText: '' });
  sandbox.getSelection = () => ({ toString: () => '', rangeCount: 0, removeAllRanges: noop });
  sandbox.matchMedia = () => ({ matches: false, media: '', addEventListener: noop, removeEventListener: noop, addListener: noop, removeListener: noop });
  sandbox.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  sandbox.IntersectionObserver = class { observe() {} unobserve() {} disconnect() {} };
  sandbox.requestIdleCallback = cb => setTimeout(cb, 100);
  sandbox.cancelIdleCallback = clearTimeout;
  sandbox.queueMicrotask = cb => setImmediate(cb);
  sandbox.customElements = { define: noop, get: () => undefined, upgrade: noop, whenDefined: () => Promise.resolve() };
  sandbox.sessionStorage = { getItem: () => null, setItem: noop, removeItem: noop, clear: noop, key: () => null, length: 0 };
  sandbox.devicePixelRatio = 1;
  sandbox.origin = 'https://juejin.cn';
  sandbox.top = sandbox;
  sandbox.parent = sandbox;
  sandbox.frames = sandbox;
  sandbox.name = '';
  sandbox.closed = false;
  sandbox.outerWidth = 1920;
  sandbox.outerHeight = 1040;
  sandbox.isSecureContext = true;
  sandbox.crossOriginIsolated = false;
  sandbox.self = sandbox;
  sandbox.window = sandbox; sandbox.global = sandbox; sandbox.globalThis = sandbox;
  sandbox.fetch = fetchCapture;

  const ctx = vm.createContext(sandbox);
  const code = fs.readFileSync(__dirname + '\\bdms.js', 'utf8');
  vm.runInContext(code, ctx, { filename: 'bdms.js', timeout: 30000 });
  const paths = pathsArg ? pathsArg.split(',') : ['/growth_api/v1/check_in', '/growth_api/v1/lottery/draw', '/growth_api/v1/get_cur_point'];
  sandbox.bdms.init({ aid: 2608, paths });
  const drawUrl = u + '&a_bogus=PENDING';
  sandbox.fetch(drawUrl, { method: 'POST', body: payload });
  setTimeout(() => {
    if (RESULT) {
      console.log('SIGN ' + RESULT.bogus);
      process.exit(0);
    } else {
      console.log('SIGN ERROR_NO_RESULT');
      process.exit(1);
    }
  }, 2000);
  setTimeout(() => { console.log('SIGN ERROR_TIMEOUT'); process.exit(1); }, 8000);
}

main();