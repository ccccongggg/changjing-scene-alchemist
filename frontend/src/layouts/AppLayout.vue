<template>
  <div class="app-layout">
    <header class="topbar">
      <div class="topbar__inner">
        <router-link to="/" class="brand">
          <span class="brand__logo">场景炼金师</span>
        </router-link>

        <nav class="nav">
          <router-link to="/" class="nav__link" exact-active-class="is-active">首页</router-link>
          <router-link to="/bench" class="nav__link" active-class="is-active">收藏台</router-link>
          <router-link to="/library" class="nav__link" active-class="is-active">方案库</router-link>
          <router-link to="/adapt/1" class="nav__link" active-class="is-active">场景工坊</router-link>
        </nav>

        <div class="topbar__right">
          <div class="search">
            <i class="search__ico">⌕</i>
            <input
              class="search__input"
              type="text"
              placeholder="搜索场景 / 方案 / 帖子"
            />
          </div>
          <button class="avatar" title="用户中心">CC</button>
          <button class="ask" title="提一个问题">提问</button>
        </div>
      </div>
    </header>

    <main class="content" :class="{ 'content--home': isHome }">
      <slot />
    </main>

    <footer class="footer">
      <div class="footer__inner">
        <span class="footer__brand">场景炼金师</span>
        <span class="footer__tag">同帖千面 · 真实场景炼金</span>
        <span class="footer__hint">真实场景 × AI 起草 × 人验证</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isHome = computed(() => route.path === '/')
</script>

<style scoped>
.app-layout {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ----- 顶栏：知乎风 ----- */
.topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--bg-2);
  border-bottom: 1px solid var(--border);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.topbar__inner {
  max-width: var(--maxw);
  margin: 0 auto;
  height: 52px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 24px;
}

.brand {
  display: inline-flex;
  align-items: center;
  font-weight: 800;
  font-size: 16px;
  color: var(--zh-blue);
  letter-spacing: 0.2px;
}
.brand__logo {
  color: inherit;
}

.nav {
  display: flex;
  gap: 4px;
  margin: 0 auto;
}
.nav__link {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-2);
  transition: color 0.15s ease, background 0.15s ease;
}
.nav__link:hover {
  color: var(--zh-blue);
  background: var(--zh-blue-soft);
}
.nav__link.is-active {
  color: var(--zh-blue);
  font-weight: 600;
}
.nav__link.is-active::after {
  content: "";
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: -10px;
  height: 3px;
  border-radius: 2px;
  background: var(--zh-blue);
}

/* 右侧 */
.topbar__right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.search {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  width: 200px;
  height: 34px;
  padding: 0 12px;
  border-radius: 4px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  transition: border-color 0.15s ease, background 0.15s ease;
}
.search:focus-within {
  background: var(--bg-2);
  border-color: var(--zh-blue-line-strong);
}
.search__ico {
  color: var(--text-3);
  font-size: 14px;
}
.search__input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: var(--text);
  font-family: inherit;
}
.search__input::placeholder {
  color: var(--text-3);
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: var(--zh-blue-soft);
  color: var(--zh-blue);
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s ease;
}
.avatar:hover {
  background: var(--zh-blue-line-strong);
  color: #ffffff;
}
.ask {
  height: 32px;
  padding: 0 16px;
  border-radius: 4px;
  border: none;
  background: var(--zh-blue);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s ease;
}
.ask:hover {
  background: var(--zh-blue-hover);
}

/* ----- 内容区 ----- */
.content {
  flex: 1;
  width: 100%;
  max-width: var(--maxw);
  margin: 0 auto;
  padding: 24px 24px 64px;
}
.content--home {
  padding: 0;
  max-width: none;
}

/* ----- 页脚 ----- */
.footer {
  border-top: 1px solid var(--border);
  background: var(--bg-2);
}
.footer__inner {
  max-width: var(--maxw);
  margin: 0 auto;
  padding: 18px 24px;
  display: flex;
  align-items: center;
  gap: 18px;
  font-size: 13px;
  color: var(--text-3);
}
.footer__brand {
  color: var(--text);
  font-weight: 700;
}
.footer__tag {
  color: var(--zh-blue);
}
.footer__hint {
  margin-left: auto;
}

@media (max-width: 760px) {
  .nav {
    display: none;
  }
  .search {
    width: 140px;
  }
  .footer__hint {
    display: none;
  }
}
</style>
