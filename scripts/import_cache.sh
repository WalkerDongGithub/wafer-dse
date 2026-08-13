#!/usr/bin/env bash
# 导入外部缓存 —— 把另一台机器拷来的 .cache 目录合并进本机缓存.
#
# 用法:
#   ./scripts/import_cache.sh <源缓存目录>
#   或: make import-cache SRC=<源缓存目录>
#
# 缓存条目 key 是内容哈希、无路径依赖，拷过来即命中。
# 合并式导入：已存在的条目跳过，不覆盖本机缓存。
set -euo pipefail

SRC="${1:-}"
if [ -z "$SRC" ]; then
    echo "用法: ./scripts/import_cache.sh <源缓存目录>"
    exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DST="$ROOT/exp/output/.cache"

if [ ! -d "$SRC" ]; then
    echo "错误: 源目录不存在: $SRC"
    exit 1
fi

mkdir -p "$DST"

added=0
skipped=0
broken=0

for entry in "$SRC"/*/; do
    name=$(basename "$entry")
    if [ ! -f "$entry/meta.json" ]; then
        echo "跳过（不是缓存条目，无 meta.json）: $name"
        broken=$((broken + 1))
        continue
    fi
    if [ -d "$DST/$name" ]; then
        skipped=$((skipped + 1))
        continue
    fi
    cp -r "$entry" "$DST/$name"
    added=$((added + 1))
done

echo "导入完成: 新增 $added 个条目, 已存在跳过 $skipped, 非缓存 $broken"
echo "目标: $DST"
