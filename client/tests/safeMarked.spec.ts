import { describe, expect, it } from "vitest";
import { safeMarked } from "../src/utils/safeMarked";

describe("safeMarked", () => {
  it("renders basic markdown", () => {
    const html = safeMarked("**加粗** 与 `code`");
    expect(html).toContain("<strong>加粗</strong>");
  });

  it("strips script tags", () => {
    const html = safeMarked('hello <script>alert(1)</script> world');
    expect(html).not.toContain("<script");
    expect(html).not.toContain("alert(1)");
  });

  it("strips inline event handlers", () => {
    const html = safeMarked('<img src=x onerror="alert(1)">');
    expect(html).not.toContain("onerror");
  });

  it("strips javascript: links", () => {
    const html = safeMarked("[click](javascript:alert(1))");
    expect(html).not.toContain("javascript:");
  });

  it("returns empty string for falsy input", () => {
    expect(safeMarked("")).toBe("");
    expect(safeMarked(null)).toBe("");
    expect(safeMarked(undefined)).toBe("");
  });

  it("preserves AI resume bullets", () => {
    const html = safeMarked("- 负责后端接口开发\n- 参与数据库优化");
    expect(html).toContain("<li>负责后端接口开发</li>");
  });
});
