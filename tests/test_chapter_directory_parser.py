# -*- coding: utf-8 -*-
import unittest

from chapter_directory_parser import (
    extract_explicit_chapter_number,
    get_chapter_info_from_blueprint,
    get_chapter_outline_context,
    parse_chapter_blueprint,
)


class ChapterDirectoryParserTest(unittest.TestCase):
    def test_parses_adjacent_chinese_chapters_without_blank_lines(self):
        blueprint = """第1章 - [紫极光下的预兆]
本章定位：[开篇/事件]
核心作用：[引出异常]
悬念密度：[渐进]
伏笔操作：埋设(A线索)
认知颠覆：★☆☆☆☆
本章简述：[主角发现天空异象]
第2章 - [失落档案]
本章定位：[调查/角色]
核心作用：[揭示旧案]
悬念密度：[紧凑]
伏笔操作：强化(A线索)
认知颠覆：★★☆☆☆
本章简述：[主角找到关键档案]"""

        chapters = parse_chapter_blueprint(blueprint)

        self.assertEqual(2, len(chapters))
        self.assertEqual(1, chapters[0]["chapter_number"])
        self.assertEqual("紫极光下的预兆", chapters[0]["chapter_title"])
        self.assertEqual("开篇/事件", chapters[0]["chapter_role"])
        self.assertEqual("主角发现天空异象", chapters[0]["chapter_summary"])
        self.assertEqual(2, chapters[1]["chapter_number"])
        self.assertEqual("失落档案", chapters[1]["chapter_title"])
        self.assertEqual("揭示旧案", chapters[1]["chapter_purpose"])

    def test_parses_markdown_and_colon_style_chinese_output(self):
        blueprint = """## 第 3 章：《潮汐门》
- 章节定位：转折/世界观
- 核心作用：打开新的空间规则
- 悬念密度：爆发
- 伏笔设计：回收(B矛盾)
- 转折程度：★★★★☆
- 章节简述：潮汐门打开后，主角发现旧盟友隐瞒真相。"""

        chapter = get_chapter_info_from_blueprint(blueprint, 3)

        self.assertEqual("潮汐门", chapter["chapter_title"])
        self.assertEqual("转折/世界观", chapter["chapter_role"])
        self.assertEqual("回收(B矛盾)", chapter["foreshadowing"])
        self.assertEqual("★★★★☆", chapter["plot_twist_level"])
        self.assertEqual(
            "潮汐门打开后，主角发现旧盟友隐瞒真相。",
            chapter["chapter_summary"],
        )

    def test_parses_english_chapter_blueprint(self):
        blueprint = """Chapter 4 - [The Glass Archive]
Chapter role: Investigation / character
Core function: Reveal the hidden contract
Suspense density: Rising
Foreshadowing: Seed(C clue)
Cognitive subversion: ★★★☆☆
Chapter summary: The protagonist decodes the archive and changes allegiance."""

        chapter = get_chapter_info_from_blueprint(blueprint, 4)

        self.assertEqual("The Glass Archive", chapter["chapter_title"])
        self.assertEqual("Investigation / character", chapter["chapter_role"])
        self.assertEqual("Reveal the hidden contract", chapter["chapter_purpose"])
        self.assertEqual("Rising", chapter["suspense_level"])
        self.assertEqual("Seed(C clue)", chapter["foreshadowing"])
        self.assertEqual(
            "The protagonist decodes the archive and changes allegiance.",
            chapter["chapter_summary"],
        )

    def test_returns_default_info_when_chapter_is_missing(self):
        chapter = get_chapter_info_from_blueprint("第1章 - 起点", 9)

        self.assertEqual(9, chapter["chapter_number"])
        self.assertEqual("第9章", chapter["chapter_title"])
        self.assertEqual("", chapter["chapter_summary"])

    def test_extracts_single_markdown_chapter_outline_context(self):
        blueprint = """# 第1章 - 逆生晶簇
**本章简述**：陈凡发现逆生晶簇。

# 第2章 - 骸骨低语
**本章定位**：事件/核心揭示
**本章简述**：陈凡挖出玄霄遗骸。

# 第3章 - 三方相遇
**本章简述**：铁骨引爆矿洞制造混乱。"""

        context = get_chapter_outline_context(blueprint, 2)

        self.assertIn("# 第2章 - 骸骨低语", context)
        self.assertIn("陈凡挖出玄霄遗骸", context)
        self.assertNotIn("# 第3章 - 三方相遇", context)

    def test_extracts_explicit_chapter_number_from_generated_heading(self):
        self.assertEqual(3, extract_explicit_chapter_number("# 第3章 三方相遇\n正文"))
        self.assertEqual(4, extract_explicit_chapter_number("## Chapter 4 - The Glass Archive\nBody"))
        self.assertIsNone(extract_explicit_chapter_number("矿道在身后崩塌，碎石如雨般砸落。"))


if __name__ == "__main__":
    unittest.main()
