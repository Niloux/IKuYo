<template>
  <div class="about">
    <div class="about-hero">
      <h1 class="about-title">关于 IKuYo</h1>
      <p class="about-subtitle">专业的动漫追番助手</p>
    </div>

    <div class="about-content">
      <section class="feature-section">
        <h2 class="section-title">核心功能</h2>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">📅</div>
            <h3>每日放送</h3>
            <p>实时获取最新的动漫放送时间表，不错过任何精彩内容</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <h3>智能搜索</h3>
            <p>快速找到想看的动漫，支持多种搜索条件和筛选</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">⭐</div>
            <h3>评分系统</h3>
            <p>查看动漫评分和评价，发现高质量的作品</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📱</div>
            <h3>响应式设计</h3>
            <p>完美适配各种设备，随时随地享受追番乐趣</p>
          </div>
        </div>
      </section>

      <section class="info-section">
        <h2 class="section-title">技术栈</h2>
        <div class="tech-tags">
          <span class="tech-tag">Vue 3</span>
          <span class="tech-tag">TypeScript</span>
          <span class="tech-tag">FastAPI</span>
          <span class="tech-tag">Python</span>
          <span class="tech-tag">Scrapy</span>
        </div>
      </section>

      <section class="contact-section">
        <h2 class="section-title">联系我们</h2>
        <p class="contact-text">
          如果您有任何建议或发现了问题，欢迎与我们联系。我们致力于为用户提供最好的追番体验。
        </p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.about {
  max-width: 800px;
  margin: 0 auto;
}

.about-hero {
  text-align: center;
  margin-bottom: 3rem;
  padding: 2rem 0;
}

.about-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-text-dark);
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.about-subtitle {
  font-size: 1.2rem;
  color: var(--color-text-light);
}

.about-content {
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--color-text-dark);
  margin-bottom: 1.5rem;
  text-align: center;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.feature-card {
  background: var(--color-bg-white);
  padding: 2rem;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  text-align: center;
  transition: transform var(--transition-normal);
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.feature-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-dark);
  margin-bottom: 0.75rem;
}

.feature-card p {
  color: var(--color-text-light);
  line-height: 1.6;
}

.info-section {
  text-align: center;
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
}

.tech-tag {
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  color: white;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: 0.9rem;
}

.contact-section {
  text-align: center;
  background: var(--color-bg-white);
  padding: 2rem;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.contact-text {
  color: var(--color-text-light);
  line-height: 1.7;
  font-size: 1.1rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .about-title {
    font-size: 2rem;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .tech-tags {
    gap: 0.5rem;
  }

  .tech-tag {
    font-size: 0.8rem;
    padding: 0.4rem 0.8rem;
  }
}
</style>
