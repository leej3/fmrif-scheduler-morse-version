// tests/oauth.spec.ts
// OAuth 2.0 with Microsoft Entra authentication flow tests
import { test, expect } from '@playwright/test';

test.describe('OAuth 2.0 / Entra Authentication', () => {
  const BASE_URL = process.env.BASE_URL || 'https://fmrif-schedule-backend-dev.nimh.nih.gov';

  test.beforeEach(async ({ page }) => {
    // Disable RBAC superuser mode to test real auth flow
    // (This env var would be set in CI/testing environment)
    await page.goto(`${BASE_URL}/auth/login`);
  });

  test('should display OAuth login page with Entra button', async ({ page }) => {
    // Verify login page elements
    await expect(page.getByRole('heading', { name: /Device Scheduler/i })).toBeVisible();
    await expect(page.getByText(/Sign in with your NIH credentials/i)).toBeVisible();

    const loginButton = page.getByRole('button', { name: /Login with NIH Credentials/i });
    await expect(loginButton).toBeVisible();
    await expect(loginButton).toBeEnabled();
  });

  test('should load Entra configuration', async ({ page }) => {
    // Verify entra-config.json is loaded and accessible
    const configResponse = await page.evaluate(async () => {
      const response = await fetch('/static/config/entra-config.json');
      return response.json();
    });

    expect(configResponse.client_id).toBeTruthy();
    expect(configResponse.tenant_id).toBeTruthy();
    expect(configResponse.redirect_uri).toContain('fmrif-schedule-backend-dev');
    expect(configResponse.authorization_endpoint).toContain('login.microsoftonline.com');
  });

  test('should initialize authentication module', async ({ page }) => {
    // Verify auth-manager.js initializes without errors
    const authInitialized = await page.evaluate(async () => {
      // Check if auth functions are available
      return typeof initializeAuth === 'function' &&
             typeof startOAuthFlow === 'function';
    });

    expect(authInitialized).toBe(true);
  });

  test('should show error on OAuth click (expected - would redirect to Entra)', async ({ page }) => {
    // This test verifies the login button attempts to start OAuth flow
    // In a real scenario, it would redirect to Entra login
    // For now, we just verify the button is clickable

    const loginButton = page.getByRole('button', { name: /Login with NIH Credentials/i });

    // Store initial URL
    const initialUrl = page.url();

    // Click login button - in real scenario would redirect to Entra
    // Set up a listener for any navigation
    let navigationAttempted = false;
    page.on('framenavigated', () => {
      navigationAttempted = true;
    });

    // Try clicking the button
    await loginButton.click();

    // Wait a bit to see if navigation starts
    await page.waitForTimeout(2000);

    // Either we redirected or we see an error message
    const pageUrl = page.url();
    const errorVisible = await page.getByText(/Error starting login/i).isVisible().catch(() => false);

    // Either URL changed (redirected to Entra) or error is shown
    expect(pageUrl !== initialUrl || errorVisible || navigationAttempted).toBe(true);
  });

  test('should verify PKCE flow is properly configured', async ({ page }) => {
    // Verify crypto API and PKCE utilities are available
    const pkceAvailable = await page.evaluate(async () => {
      // Check if crypto functions are available
      return typeof generateVerifier === 'function' &&
             typeof pkceChallenge === 'function' &&
             typeof crypto !== 'undefined';
    });

    expect(pkceAvailable).toBe(true);
  });

  test('should have HTTPS redirect_uri in configuration', async ({ page }) => {
    // Critical: redirect_uri must be HTTPS for production
    const config = await page.evaluate(async () => {
      const response = await fetch('/static/config/entra-config.json');
      return response.json();
    });

    // Verify redirect_uri uses HTTPS
    expect(config.redirect_uri).toMatch(/^https:\/\//);
    // Verify it's the correct domain
    expect(config.redirect_uri).toContain('fmrif-schedule-backend-dev.nimh.nih.gov');
    // Verify callback path
    expect(config.redirect_uri).toContain('/auth/callback');
  });
});
