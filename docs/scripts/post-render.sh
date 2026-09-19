#!/bin/bash

# Optional aggregation for LLMS export similar to inspect_ai; noop by default
if [ "$QUARTO_PROJECT_RENDER_ALL" = "1" ]; then
    files=(
        "index"
        "reference/metrics"
        "reference/scorers"
        "reference/solvers"
        "reference/solvers/exports"
        "reference/solvers/imports"
        "reference/solvers/diffs"
        "reference/tools"
        "reference/datasets"
        "reference/fixtures"
        "reference/utils/coding"
        "reference/utils/collections"
        "reference/utils/databases"
        "reference/utils/eval"
        "reference/utils/evals"
        "reference/utils/filesystem"
        "reference/utils/format"
        "reference/utils/math"
        "reference/utils/parse"
        "reference/utils/sandbox"
    )
    llms_full="_site/llms-full.txt"
    rm -f "${llms_full}"
    mv _quarto.yml _quarto.yml.bak
    for file in "${files[@]}"; do
        echo "llms: ${file}.qmd"
        quarto render "${file}.qmd" --to gfm-raw_html --quiet --no-execute
        output_file="${file}.md"
        cat "${output_file}" >> "${llms_full}"
        echo "" >> "${llms_full}"
        mv $output_file "_site/${file}.html.md"
    done
    mv _quarto.yml.bak _quarto.yml
fi
