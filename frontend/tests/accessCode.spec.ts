import { beforeEach, describe, expect, it } from "vitest";
import { getAccessCode, setAccessCode } from "../src/utils/accessCode";

describe("accessCode storage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("round-trips a code", () => {
    setAccessCode("secret-123");
    expect(getAccessCode()).toBe("secret-123");
  });

  it("clears the code when empty", () => {
    setAccessCode("secret-123");
    setAccessCode("");
    expect(getAccessCode()).toBe("");
    expect(localStorage.getItem("accessCode")).toBeNull();
  });

  it("defaults to empty when unset", () => {
    expect(getAccessCode()).toBe("");
  });
});
