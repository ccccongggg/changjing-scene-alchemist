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
          <router-link to="/starmap" class="nav__link" active-class="is-active">星图</router-link>
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

        <button
          class="menu-btn"
          :class="{ 'is-open': mobileNavOpen }"
          :aria-expanded="mobileNavOpen"
          aria-label="打开导航菜单"
          @click="mobileNavOpen = !mobileNavOpen"
        >
          <span />
          <span />
          <span />
        </button>
      </div>

      <!-- 移动端下拉导航 -->
      <nav class="mnav" :class="{ 'mnav--open': mobileNavOpen }">
        <router-link
          v-for="l in navLinks"
          :key="l.to"
          :to="l.to"
          class="mnav__link"
          :class="{ 'is-active': isActive(l) }"
          @click="mobileNavOpen = false"
        >
          {{ l.label }}
        </router-link>
      </nav>
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
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isHome = computed(() => route.path === '/')

const navLinks = [
  { to: '/', label: '首页', exact: true },
  { to: '/bench', label: '收藏台' },
  { to: '/starmap', label: '星图' },
  { to: '/library', label: '方案库' },
  { to: '/adapt/1', label: '场景工坊' }
]

const mobileNavOpen = ref(false)

const isActive = (l) =>
  l.exact ? route.path === l.to : route.path.startsWith(l.to)

// 路由切换后自动收起移动端菜单
watch(() => route.fullPath, () => {
  mobileNavOpen.value = false
})
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

/* ----- 移动端汉堡按钮（桌面隐藏） ----- */
.menu-btn {
  display: none;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  width: 36px;
  height: 36px;
  padding: 0 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-2);
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}
.menu-btn span {
  display: block;
  height: 2px;
  width: 100%;
  border-radius: 2px;
  background: var(--text-2);
  transition: transform 0.22s ease, opacity 0.18s ease;
}
.menu-btn.is-open {
  border-color: var(--zh-blue-line-strong);
  background: var(--zh-blue-soft);
}
.menu-btn.is-open span {
  background: var(--zh-blue);
}
.menu-btn.is-open span:nth-child(1) {
  transform: translateY(6px) rotate(45deg);
}
.menu-btn.is-open span:nth-child(2) {
  opacity: 0;
}
.menu-btn.is-open span:nth-child(3) {
  transform: translateY(-6px) rotate(-45deg);
}

/* ----- 移动端下拉导航（桌面隐藏） ----- */
.mnav {
  display: none;
  flex-direction: column;
  gap: 2px;
  padding: 6px 14px 12px;
  background: var(--bg-2);
  border-top: 1px solid var(--border);
  box-shadow: 0 8px 18px -12px rgba(0, 0, 0, 0.25);
}
.mnav__link {
  display: flex;
  align-items: center;
  min-height: 44px;
  padding: 0 12px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-2);
}
.mnav__link.is-active {
  color: var(--zh-blue);
  font-weight: 700;
  background: var(--zh-blue-soft);
}

/* ----- 内容区 ----- */
.content {
  flex: 1;
  width: 100%;
  max-width: var(--maxw);
  margin: 0 auto;
  padding: 24px 24px 64px;
  min-width: 0;
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
  flex-wrap: wrap;
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

/* ===== 移动端：横向空间不足，导航收进汉堡菜单 ===== */
@media (max-width: 860px) {
  .nav {
    display: none;
  }
  .topbar__inner {
    height: 52px;
    padding: 0 14px;
    gap: 10px;
  }
  .brand {
    font-size: 15px;
    margin-right: auto;
  }
  .topbar__right {
    gap: 8px;
  }
  .search {
    display: none;
  }
  .ask {
    padding: 0 12px;
    font-size: 13px;
  }
  .menu-btn {
    display: flex;
  }
  .mnav--open {
    display: flex;
  }
  .content {
    padding: 16px 14px 48px;
  }
  .footer__inner {
    padding: 16px 14px;
    gap: 10px;
  }
  .footer__hint {
    display: none;
  }
}

@media (max-width: 380px) {
  .brand {
    font-size: 14px;
  }
  .avatar {
    display: none;
  }
  .content {
    padding: 14px 12px 44px;
  }
}

/* ===== 刘海屏安全区（横屏时左右不被挖孔遮挡） ===== */
@supports (padding: max(0px)) {
  @media (max-width: 860px) {
    .topbar__inner {
      padding-left: max(14px, env(safe-area-inset-left));
      padding-right: max(14px, env(safe-area-inset-right));
    }
    .content {
      padding-left: max(14px, env(safe-area-inset-left));
      padding-right: max(14px, env(safe-area-inset-right));
    }
    .mnav {
      padding-left: max(14px, env(safe-area-inset-left));
      padding-right: max(14px, env(safe-area-inset-right));
    }
    .footer__inner {
      padding-left: max(14px, env(safe-area-inset-left));
      padding-right: max(14px, env(safe-area-inset-right));
      padding-bottom: max(16px, env(safe-area-inset-bottom));
    }
  }
}
</style>
