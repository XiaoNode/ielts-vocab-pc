const store = {};
globalThis.localStorage = {
  getItem: (k) => (k in store ? store[k] : null),
  setItem: (k, v) => { store[k] = String(v); },
  removeItem: (k) => { delete store[k]; },
};
const m = await import('./src/store.js');
let favs = m.loadFavorites();
console.log('初始收藏:', JSON.stringify(favs));
favs = m.toggleFavorite(favs, 'apple');
favs = m.toggleFavorite(favs, 'banana');
m.saveFavorites(favs);
console.log('收藏后 isFav(apple)=', m.isFavorite(favs, 'apple'), 'isFav(pear)=', m.isFavorite(favs, 'pear'));
const reloaded = m.loadFavorites();
console.log('重载收藏:', JSON.stringify(reloaded), '(应 [apple,banana])');
let favs2 = m.toggleFavorite(reloaded, 'apple');
console.log('取消apple后:', JSON.stringify(favs2), '(应 [banana])');
let prog = {};
prog['apple'] = m.applyResult(null, 'zhan', true);
const stats = m.computeStats(prog);
console.log('统计:', JSON.stringify(stats));
console.log('OK');
