import { describe, expect, it } from "vitest";
import { DEFAULT_SECTION_ORDER, normalizeSectionOrder } from "../src/constants/sectionOrder";
import { moveItem } from "../src/utils/reorder";

describe("normalizeSectionOrder", () => {
  it("returns the default order for empty input", () => {
    expect(normalizeSectionOrder(null)).toEqual(DEFAULT_SECTION_ORDER);
    expect(normalizeSectionOrder([])).toEqual(DEFAULT_SECTION_ORDER);
  });

  it("keeps known keys in given order", () => {
    const order = normalizeSectionOrder(["summary", "education"]);
    expect(order.slice(0, 2)).toEqual(["summary", "education"]);
    expect(order).toHaveLength(DEFAULT_SECTION_ORDER.length);
  });

  it("drops unknown keys and duplicates, appends missing sections", () => {
    const order = normalizeSectionOrder(["summary", "bogus" as never, "summary", "skills"]);
    expect(order).toEqual([
      "summary",
      "skills",
      "personalInfo",
      "education",
      "projects",
      "workExperience",
      "honors",
    ]);
  });
});

describe("moveItem", () => {
  it("moves items within bounds", () => {
    const list = ["a", "b", "c"];
    moveItem(list, 0, 2);
    expect(list).toEqual(["b", "c", "a"]);
  });

  it("is a no-op when from === to or out of range", () => {
    const list = ["a", "b"];
    moveItem(list, 1, 1);
    moveItem(list, 9, 0);
    expect(list).toEqual(["a", "b"]);
  });
});
