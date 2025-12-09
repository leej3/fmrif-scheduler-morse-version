/**
 * OAuth 2.0 Utility Functions
 * Handles PKCE (Proof Key for Code Exchange) and authorization code extraction
 * for Microsoft Entra OAuth 2.0 / OIDC authentication flows.
 */

/**
 * Base64URL encode an array buffer
 * Used for PKCE code challenge encoding
 *
 * @param {ArrayBuffer} arrayBuffer - The data to encode
 * @returns {string} Base64URL encoded string
 * @private
 */
function base64UrlEncode(arrayBuffer) {
  const bytes = new Uint8Array(arrayBuffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+/g, "");
}

/**
 * Generate a PKCE verifier string
 *
 * The PKCE (RFC 7636) verifier is a cryptographically random string of 43-128
 * characters using the unreserved characters [A-Z] [a-z] [0-9] - . _ ~
 *
 * This implementation generates a 64-character verifier, which provides
 * sufficient entropy for browser-based OAuth flows.
 *
 * @param {number} [length=64] - Length of the verifier (default 64)
 * @returns {string} Random PKCE verifier string
 *
 * @example
 * const verifier = generateVerifier();
 * console.log(verifier.length); // 64
 * sessionStorage.setItem('pkce_verifier', verifier);
 */
function generateVerifier(length = 64) {
  const charset =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~";
  const randomValues = new Uint8Array(length);
  crypto.getRandomValues(randomValues);
  return Array.from(
    randomValues,
    (value) => charset[value % charset.length],
  ).join("");
}

/**
 * Generate a PKCE code challenge from a verifier
 *
 * The code challenge is the SHA-256 hash of the verifier, Base64URL encoded.
 * Used in the authorization request to bind the authorization code to the verifier.
 *
 * This is an async function because crypto.subtle.digest is async.
 *
 * @param {string} verifier - The PKCE verifier string
 * @returns {Promise<string>} Base64URL encoded SHA-256 hash of the verifier
 *
 * @example
 * const verifier = generateVerifier();
 * const challenge = await pkceChallenge(verifier);
 * // Use challenge in authorization request parameters
 */
async function pkceChallenge(verifier) {
  const data = new TextEncoder().encode(verifier);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return base64UrlEncode(digest);
}

/**
 * Extract authorization code from a redirect URL
 *
 * Handles both full redirect URLs and plain authorization codes.
 * If a full URL is provided, extracts the 'code' query parameter.
 * Otherwise, returns the value as-is (assuming it's already a plain code).
 *
 * @param {string} value - Either a full redirect URL or a plain authorization code
 * @returns {string} The authorization code (empty string if not found or invalid)
 *
 * @example
 * // Full URL
 * const url = 'https://localhost:8000?code=M.R3_...&state=xyz';
 * const code = extractCodeFromUrl(url);
 * console.log(code); // "M.R3_..."
 *
 * @example
 * // Plain code
 * const code = extractCodeFromUrl('M.R3_...');
 * console.log(code); // "M.R3_..."
 */
function extractCodeFromUrl(value) {
  if (!value) return "";
  const trimmed = value.trim();
  if (trimmed.startsWith("http")) {
    try {
      const url = new URL(trimmed);
      const code = url.searchParams.get("code");
      if (code) {
        return code;
      }
    } catch (err) {
      console.warn("Unable to parse URL", err);
    }
  }
  return trimmed;
}

// Export functions for use in other modules
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    generateVerifier,
    pkceChallenge,
    extractCodeFromUrl,
  };
}
