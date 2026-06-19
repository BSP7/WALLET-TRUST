/**
 * Shared code between client and server
 * Useful to share types between client and server
 * and/or small pure JS functions that can be used on both client and server
 */

/**
 * Example response type for /api/demo
 */
export interface DemoResponse {
  message: string;
}

/**
 * Token generation request type for /api/token/generate
 */
export interface TokenGenerateRequest {
  userId: string;
  governmentIdNumber: string;
}

/**
 * Token generation response type for /api/token/generate
 */
export interface TokenGenerateResponse {
  success: boolean;
  token?: string;
  message?: string;
}
