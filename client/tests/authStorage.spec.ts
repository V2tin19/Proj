import { beforeEach, describe, expect, it } from "vitest";
import {
  clearSession,
  getServerBase,
  getSessionUser,
  getToken,
  hasSession,
  hasSkippedAuth,
  markAuthSkipped,
  saveSession,
  setServerBase,
} from "../src/utils/auth";

describe("auth session storage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("round-trips a session", () => {
    saveSession("tok-123", { username: "alice01", role: "user" });
    expect(getToken()).toBe("tok-123");
    expect(getSessionUser()?.username).toBe("alice01");
    expect(hasSession()).toBe(true);
  });

  it("clears session on logout", () => {
    saveSession("tok-123", { username: "alice01", role: "admin" });
    clearSession();
    expect(hasSession()).toBe(false);
    expect(getSessionUser()).toBeNull();
  });

  it("anonymous skip is remembered and cleared by login", () => {
    expect(hasSkippedAuth()).toBe(false);
    markAuthSkipped();
    expect(hasSkippedAuth()).toBe(true);
    saveSession("tok-123", { username: "alice01", role: "user" });
    expect(hasSkippedAuth()).toBe(false);
  });

  it("server base trims trailing slashes and defaults to same-origin", () => {
    expect(getServerBase()).toBe("");
    setServerBase("http://192.168.1.10:8000/");
    expect(getServerBase()).toBe("http://192.168.1.10:8000");
  });

  it("rejects corrupt user payload", () => {
    localStorage.setItem("auth.user", "{broken");
    expect(getSessionUser()).toBeNull();
  });
});
