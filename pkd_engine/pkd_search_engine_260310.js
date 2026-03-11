from pathlib import Path

content = """/*
File: pkd_search_engine_260310.js
Project: Petkidipia
Purpose: Search engine for question-first discovery UX
Input:
  - user query from search input
  - optional PKDQuestionEngine instance
  - optional PKDFinderEngine instance
Output:
  - 4 suggested questions
  - routed search state
Author: Grid
*/

(function () {
  "use strict";

  const PKD_DEFAULT_LIMIT = 4;

  const PKD_QUERY_PATTERNS = [
    {
      slug: "low-shedding-dogs",
      tokens: ["털", "털안", "털 안", "털빠짐", "털 빠짐", "shedding", "털관리"],
      finder_filter: { shedding: "low" },
      route_type: "finder",
    },
    {
      slug: "apartment-dogs",
      tokens: ["아파트", "실내", "원룸", "집에서", "소형집"],
      finder_filter: { apartment: "good" },
      route_type: "finder",
    },
    {
      slug: "beginner-dogs",
      tokens: ["초보", "처음", "입문", "처음키우", "처음 키우"],
      finder_filter: { trainability: "high" },
      route_type: "finder",
    },
    {
      slug: "kid-friendly-dogs",
      tokens: ["아이", "가족", "애기", "어린이", "자녀"],
      finder_filter: { kids: "good" },
      route_type: "finder",
    },
    {
      slug: "quiet-dogs",
      tokens: ["조용", "안짖", "안 짖", "짖음", "짖지", "소음"],
      finder_filter: { barking: "low" },
      route_type: "finder",
    },
    {
      slug: "dog-grooming",
      tokens: ["미용", "목욕", "그루밍", "브러싱", "털관리"],
      finder_filter: null,
      route_type: "care",
      target_url: "/content/care/grooming.html",
    },
    {
      slug: "dog-health",
      tokens: ["질병", "건강", "아픔", "증상", "병", "피부", "슬개골"],
      finder_filter: null,
      route_type: "health",
      target_url: "/content/info/health.html",
    },
    {
      slug: "dog-training",
      tokens: ["훈련", "배변", "교육", "말안듣", "말 안 듣", "짖음훈련"],
      finder_filter: null,
      route_type: "care",
      target_url: "/content/care/training.html",
    },
  ];

  const PKD_FALLBACK_SUGGESTIONS = [
    "털 안 빠지는 강아지 견종",
    "아파트에서 키우기 좋은 강아지",
    "초보자가 키우기 좋은 강아지",
    "강아지 털 관리 방법",
  ];

  function pkdNormalizeText(text) {
    return String(text || "")
      .trim()
      .toLowerCase()
      .replace(/\\s+/g, " ");
  }

  function pkdUnique(arr) {
    return Array.from(new Set(arr.filter(Boolean)));
  }

  class PKDSearchEngine {
    constructor(options = {}) {
      this.questionEngine = options.questionEngine || null;
      this.finderEngine = options.finderEngine || null;
      this.limit = Number(options.limit || PKD_DEFAULT_LIMIT);
      this.inputSelector = options.inputSelector || "[data-pkd-search-input]";
      this.suggestionSelector = options.suggestionSelector || "[data-pkd-suggestions]";
      this.resultSelector = options.resultSelector || "[data-pkd-search-result]";
      this.onRoute = typeof options.onRoute === "function" ? options.onRoute : null;
    }

    pkdDetectTopic(query) {
      const normalized = pkdNormalizeText(query);

      for (const pattern of PKD_QUERY_PATTERNS) {
        if (pattern.tokens.some((token) => normalized.includes(pkdNormalizeText(token)))) {
          return {
            slug: pattern.slug,
            route_type: pattern.route_type,
            finder_filter: pattern.finder_filter,
            target_url: pattern.target_url || null,
          };
        }
      }

      return {
        slug: "dog-health",
        route_type: "question",
        finder_filter: null,
        target_url: null,
      };
    }

    pkdGenerateSuggestions(query, channel = "google", intent = "info", limit = this.limit) {
      const topic = this.pkdDetectTopic(query);
      let suggestions = [];

      if (
        this.questionEngine &&
        typeof this.questionEngine.pkd_build_questions === "function"
      ) {
        try {
          suggestions = this.questionEngine.pkd_build_questions({
            topic_slug: topic.slug,
            channel,
            intent,
            max_variants: limit,
          });
        } catch (error) {
          suggestions = [];
        }
      }

      if (!suggestions || !suggestions.length) {
        suggestions = this.pkdFallbackSuggestions(query, topic.slug);
      }

      return pkdUnique(suggestions).slice(0, limit);
    }

    pkdFallbackSuggestions(query, topicSlug) {
      const normalized = pkdNormalizeText(query);

      if (topicSlug === "low-shedding-dogs" || normalized.includes("털")) {
        return [
          "강아지 털 안 빠지는 견종",
          "강아지 털 많이 빠지는 이유",
          "강아지 털 관리 방법",
          "강아지 털갈이 시기",
        ];
      }

      if (topicSlug === "apartment-dogs") {
        return [
          "아파트에서 키우기 좋은 강아지",
          "원룸에서 키우기 좋은 강아지",
          "조용한 강아지 추천",
          "실내에서 키우기 좋은 견종",
        ];
      }

      if (topicSlug === "beginner-dogs") {
        return [
          "초보자가 키우기 좋은 강아지",
          "처음 키우기 쉬운 강아지",
          "훈련 쉬운 강아지 추천",
          "입문자용 반려견 추천",
        ];
      }

      if (topicSlug === "kid-friendly-dogs") {
        return [
          "아이와 키우기 좋은 강아지",
          "가족과 잘 지내는 강아지",
          "어린아이 있는 집 강아지 추천",
          "온순한 강아지 추천",
        ];
      }

      if (topicSlug === "quiet-dogs") {
        return [
          "조용한 강아지 추천",
          "잘 안 짖는 강아지",
          "아파트용 조용한 견종",
          "소음 적은 강아지",
        ];
      }

      return PKD_FALLBACK_SUGGESTIONS.slice(0, this.limit);
    }

    pkdRoute(query) {
      const topic = this.pkdDetectTopic(query);

      const route = {
        query,
        slug: topic.slug,
        route_type: topic.route_type,
        finder_filter: topic.finder_filter,
        target_url: topic.target_url,
      };

      if (topic.route_type === "finder" && this.finderEngine) {
        if (typeof this.finderEngine.pkd_apply_external_filters === "function") {
          this.finderEngine.pkd_apply_external_filters(topic.finder_filter || {});
        }
      }

      if (this.onRoute) {
        this.onRoute(route);
      }

      return route;
    }

    pkdRenderSuggestions(suggestions) {
      const container = document.querySelector(this.suggestionSelector);
      if (!container) return;

      container.innerHTML = "";

      suggestions.forEach((text) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "pkd-search-suggestion";
        button.textContent = text;
        button.setAttribute("data-pkd-suggestion", text);

        button.addEventListener("click", () => {
          const input = document.querySelector(this.inputSelector);
          if (input) input.value = text;
          const route = this.pkdRoute(text);
          this.pkdRenderRouteResult(route);
        });

        container.appendChild(button);
      });
    }

    pkdRenderRouteResult(route) {
      const container = document.querySelector(this.resultSelector);
      if (!container) return;

      if (route.route_type === "finder") {
        container.innerHTML = `
          <div class="pkd-search-route-result">
            <strong>추천 탐색:</strong> ${route.query}<br>
            <span>Finder 필터가 적용되었습니다.</span>
          </div>
        `;
        return;
      }

      if (route.target_url) {
        container.innerHTML = `
          <div class="pkd-search-route-result">
            <strong>관련 페이지:</strong>
            <a href="${route.target_url}">${route.query}</a>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="pkd-search-route-result">
          <strong>질문 확장:</strong> ${route.query}
        </div>
      `;
    }

    pkdHandleInput(value) {
      const suggestions = this.pkdGenerateSuggestions(value);
      this.pkdRenderSuggestions(suggestions);
      return suggestions;
    }

    pkdBind() {
      const input = document.querySelector(this.inputSelector);
      if (!input) return;

      input.addEventListener("input", (event) => {
        this.pkdHandleInput(event.target.value);
      });

      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          const route = this.pkdRoute(event.target.value);
          this.pkdRenderRouteResult(route);
        }
      });

      if (input.value) {
        this.pkdHandleInput(input.value);
      } else {
        this.pkdRenderSuggestions(PKD_FALLBACK_SUGGESTIONS.slice(0, this.limit));
      }
    }
  }

  window.PKDSearchEngine = PKDSearchEngine;
})();
"""

file_path = Path("/mnt/data/pkd_search_engine_260310.js")
file_path.write_text(content, encoding="utf-8")
print(file_path.as_posix())
