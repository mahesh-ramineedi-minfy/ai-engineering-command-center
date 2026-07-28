let accessToken = null;
let onExpire = null;

export function getAccessToken() {
  return accessToken;
}

export function setAccessToken(token) {
  accessToken = token;
}

export function clearAccessToken() {
  accessToken = null;
}

export function setOnSessionExpired(callback) {
  onExpire = callback;
}

export function notifySessionExpired() {
  if (onExpire) onExpire();
}
