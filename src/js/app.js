// Utility: Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Main Application Class
class AIModelsDashboard {
    constructor() {
        this.data = null;
        this.filteredModels = [];
        this.currentFilter = 'all';
        this.searchTerm = '';
        this.currentTab = 'models';
        this.selectedModels = new Set();
        this.isLoading = false;

        this.init();
    }

    async init() {
        try {
            await this.loadData();
            this.setupEventListeners();
            this.renderInitialView();
            this.setupAutoRefresh();
            this.applyTheme();
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.showError('대시보드를 초기화하는데 실패했습니다.');
        }
    }

    async loadData() {
        try {
            const response = await fetch('./data/consolidated.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.data = await response.json();
            this.filteredModels = [...this.data.models];

            console.log(`📊 Loaded ${this.data.statistics.total_models} models from ${this.data.statistics.providers} providers`);

        } catch (error) {
            console.error('Failed to load data:', error);
            // Try to load sample data
            this.loadSampleData();
        }
    }

    loadSampleData() {
        // 샘플 데이터 (실제 데이터 로드 실패시 사용)
        this.data = {
            last_updated: new Date().toISOString(),
            providers: {
                openai: { name: 'OpenAI', model_count: 7 },
                anthropic: { name: 'Anthropic', model_count: 5 },
                google: { name: 'Google AI', model_count: 6 }
            },
            models: [
                {
                    id: 'gpt-4o',
                    name: 'GPT-4o',
                    provider: 'openai',
                    description: 'Most capable model with multimodal abilities',
                    pricing: { input: 2.50, output: 10.00 },
                    context_window: 128000,
                    features: ['chat', 'vision', 'function-calling'],
                    status: 'ga'
                },
                {
                    id: 'claude-3-5-sonnet',
                    name: 'Claude 3.5 Sonnet',
                    provider: 'anthropic',
                    description: 'Most intelligent model',
                    pricing: { input: 3.00, output: 15.00 },
                    context_window: 200000,
                    features: ['chat', 'vision', 'tool-use'],
                    status: 'ga'
                }
            ],
            statistics: {
                total_models: 18,
                providers: 3,
                free_models: 2,
                paid_models: 16
            }
        };

        this.filteredModels = [...this.data.models];
        console.warn('Using sample data');
    }

    setupEventListeners() {
        // 검색 with debouncing
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            const debouncedSearch = debounce((value) => {
                this.searchTerm = value.toLowerCase();
                this.applyFilters();
            }, 250);

            searchInput.addEventListener('input', (e) => {
                this.setLoading(true);
                debouncedSearch(e.target.value);
            });
        }

        // 필터 버튼 클릭
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('filter-btn')) {
                this.handleFilterClick(e.target);
            }

            // 필터 리셋 버튼
            if (e.target.id === 'resetFiltersBtn') {
                this.resetFilters();
            }

            // 비교하기 버튼
            if (e.target.classList.contains('btn-compare')) {
                const modelId = e.target.getAttribute('data-model-id');
                this.toggleModelComparison(modelId);
            }

            // 상세보기 버튼
            if (e.target.classList.contains('btn-details')) {
                const modelId = e.target.getAttribute('data-model-id');
                this.showModelDetails(modelId);
            }

            // 모달 닫기
            if (e.target.id === 'closeModal' || e.target.id === 'modelModal') {
                this.closeModal();
            }
        });

        // 정렬
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortModels(e.target.value);
            });
        }

        // 탭 전환
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', () => {
                const tab = button.getAttribute('data-tab');
                this.switchTab(tab);
            });
        });

        // 테마 토글
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }

    renderInitialView() {
        this.updateStatistics();
        this.createFilterButtons();
        this.renderModels();
        this.updateComparisonBadge();
    }

    updateStatistics() {
        const stats = this.data.statistics;

        const totalModelsEl = document.getElementById('totalModels');
        const totalProvidersEl = document.getElementById('totalProviders');
        const freeModelsEl = document.getElementById('freeModels');
        const lastUpdatedEl = document.getElementById('lastUpdated');

        if (totalModelsEl) totalModelsEl.textContent = stats.total_models;
        if (totalProvidersEl) totalProvidersEl.textContent = stats.providers;
        if (freeModelsEl) freeModelsEl.textContent = stats.free_models;
        if (lastUpdatedEl) {
            lastUpdatedEl.textContent = new Date(this.data.last_updated).toLocaleString('ko-KR');
        }
    }

    createFilterButtons() {
        const filtersContainer = document.getElementById('filtersContainer');
        if (!filtersContainer) return;

        const providers = Object.keys(this.data.providers);

        const filters = [
            { id: 'all', label: '전체', count: this.data.statistics.total_models },
            { id: 'free', label: '무료', count: this.data.statistics.free_models },
            ...providers.map(provider => ({
                id: provider,
                label: this.data.providers[provider].name,
                count: this.data.providers[provider].model_count
            }))
        ];

        filtersContainer.innerHTML = filters.map(filter => `
            <button class="filter-btn px-4 py-2 rounded-lg text-sm font-medium transition-colors
                ${filter.id === 'all' ? 'bg-blue-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'}"
                data-filter="${filter.id}">
                ${filter.label} (${filter.count})
            </button>
        `).join('');
    }

    handleFilterClick(button) {
        // 활성 버튼 스타일 변경
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('bg-blue-500', 'text-white');
            btn.classList.add('bg-gray-200', 'dark:bg-gray-700', 'text-gray-700', 'dark:text-gray-300');
        });

        button.classList.remove('bg-gray-200', 'dark:bg-gray-700', 'text-gray-700', 'dark:text-gray-300');
        button.classList.add('bg-blue-500', 'text-white');

        this.currentFilter = button.getAttribute('data-filter');
        this.setLoading(true);
        this.applyFilters();
    }

    resetFilters() {
        this.currentFilter = 'all';
        this.searchTerm = '';
        const searchInput = document.getElementById('searchInput');
        if (searchInput) searchInput.value = '';

        const allFilter = document.querySelector('[data-filter="all"]');
        if (allFilter) this.handleFilterClick(allFilter);
    }

    applyFilters() {
        let filtered = [...this.data.models];

        // 제공업체 필터
        if (this.currentFilter !== 'all') {
            if (this.currentFilter === 'free') {
                filtered = filtered.filter(model => {
                    const inputPrice = model.pricing?.input || model.input_price || 0;
                    return inputPrice === 0;
                });
            } else {
                filtered = filtered.filter(model =>
                    model.provider === this.currentFilter
                );
            }
        }

        // 검색 필터
        if (this.searchTerm) {
            filtered = filtered.filter(model => {
                const searchableText = [
                    model.name,
                    model.description,
                    model.provider,
                    ...(model.features || [])
                ].join(' ').toLowerCase();

                return searchableText.includes(this.searchTerm);
            });
        }

        this.filteredModels = filtered;
        this.updateResultCount();
        this.announceResults();
        this.renderModels();
    }

    updateResultCount() {
        const count = this.filteredModels.length;
        const total = this.data.models.length;
        const countEl = document.getElementById('resultCount');
        if (countEl) {
            countEl.textContent = `${count}개 / 총 ${total}개 모델`;
        }
    }

    announceResults() {
        // Can be implemented for screen readers
    }

    setLoading(loading) {
        this.isLoading = loading;
        const loadingIndicator = document.getElementById('loadingIndicator');
        const modelsGrid = document.getElementById('modelsGrid');

        if (loadingIndicator) {
            if (loading) {
                loadingIndicator.classList.remove('hidden');
                if (modelsGrid) modelsGrid.classList.add('opacity-50');
            } else {
                loadingIndicator.classList.add('hidden');
                if (modelsGrid) modelsGrid.classList.remove('opacity-50');
            }
        }

        if (this.currentTab === 'providers') {
            this.renderProvidersLoading(loading);
        }
    }

    renderProvidersLoading(loading) {
        const providersView = document.getElementById('providersView');
        if (!providersView) return;

        if (loading) {
            // Show skeleton loading cards
            providersView.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    ${Array(6).fill(0).map(() => `
                        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border-2 border-gray-200 dark:border-gray-700 p-6 animate-pulse">
                            <div class="flex items-center justify-between mb-4">
                                <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
                                <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                            </div>
                            <div class="space-y-3 mb-4">
                                <div class="flex items-center justify-between">
                                    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
                                    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                                </div>
                                <div class="flex items-center justify-between">
                                    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                                    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
                                </div>
                                <div class="flex items-center justify-between">
                                    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                                    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-28"></div>
                                </div>
                            </div>
                            <div class="h-10 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
                            <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                                <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20 mb-2"></div>
                                <div class="space-y-2">
                                    <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
                                    <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
                                    <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            // Render actual providers when not loading
            this.renderProviders();
        }
    }

    sortModels(sortBy) {
        const sorted = [...this.filteredModels];

        switch (sortBy) {
            case 'name':
                sorted.sort((a, b) => a.name.localeCompare(b.name));
                break;
            case 'price-asc':
                sorted.sort((a, b) => {
                    const priceA = a.pricing?.input || a.input_price || 0;
                    const priceB = b.pricing?.input || b.input_price || 0;
                    return priceA - priceB;
                });
                break;
            case 'price-desc':
                sorted.sort((a, b) => {
                    const priceA = a.pricing?.input || a.input_price || 0;
                    const priceB = b.pricing?.input || b.input_price || 0;
                    return priceB - priceA;
                });
                break;
            case 'context':
                sorted.sort((a, b) => (b.context_window || 0) - (a.context_window || 0));
                break;
            case 'release':
                sorted.sort((a, b) => {
                    const dateA = new Date(a.release_date || '2020-01-01');
                    const dateB = new Date(b.release_date || '2020-01-01');
                    return dateB - dateA;
                });
                break;
        }

        this.filteredModels = sorted;
        this.renderModels();
    }

    renderModels() {
        const modelsGrid = document.getElementById('modelsGrid');
        if (!modelsGrid) return;

        if (this.filteredModels.length === 0) {
            const hasActiveFilters = this.currentFilter !== 'all' || this.searchTerm !== '';
            modelsGrid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <svg class="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">검색 결과가 없습니다</h3>
                    <p class="text-gray-600 dark:text-gray-400 mb-4">
                        ${hasActiveFilters
                            ? '현재 필터 조건에 맞는 모델을 찾을 수 없습니다.'
                            : '표시할 모델이 없습니다.'}
                    </p>
                    ${hasActiveFilters ? `
                        <button
                            id="resetFiltersBtn"
                            class="inline-flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors"
                            aria-label="필터 초기화"
                        >
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                            </svg>
                            필터 초기화
                        </button>
                    ` : ''}
                </div>
            `;
            this.setLoading(false);
            return;
        }

        modelsGrid.innerHTML = this.filteredModels.map(model =>
            this.createModelCard(model)
        ).join('');

        this.setLoading(false);
    }

    createModelCard(model) {
        const provider = this.data.providers[model.provider] || { name: model.provider };
        const pricing = model.pricing || {
            input: model.input_price || 0,
            output: model.output_price || 0
        };

        const providerColors = {
            openai: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
            anthropic: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
            google: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
            openrouter: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
            deepseek: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
            xai: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
            mistral: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
            cohere: 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200',
            huggingface: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
            meta: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
        };

        const statusColors = {
            ga: 'bg-green-100 text-green-800',
            beta: 'bg-yellow-100 text-yellow-800',
            preview: 'bg-orange-100 text-orange-800',
            experimental: 'bg-purple-100 text-purple-800',
            deprecated: 'bg-red-100 text-red-800'
        };

        const statusLabels = {
            ga: 'GA',
            beta: 'Beta',
            preview: 'Preview',
            experimental: 'Experimental',
            deprecated: 'Deprecated'
        };

        // 여러 제공업체에서 제공되는 경우
        const availableProviders = model.available_providers || [model.provider];
        const hasMultipleProviders = availableProviders.length > 1;

        const isSelected = this.selectedModels.has(model.id);

        return `
            <article class="model-card bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow" aria-label="${model.name} 모델 정보">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex flex-wrap items-center gap-2">
                        ${hasMultipleProviders ? `
                            <div class="flex items-center gap-1 px-2 py-1 bg-blue-50 dark:bg-blue-900/20 rounded">
                                <span class="text-xs font-medium text-blue-700 dark:text-blue-300">다중 제공업체:</span>
                                ${availableProviders.slice(0, 3).map(p => {
                                    const pInfo = this.data.providers[p] || { name: p };
                                    return `<span class="px-1.5 py-0.5 text-xs font-medium rounded ${providerColors[p] || 'bg-gray-100 text-gray-800'}">${pInfo.name}</span>`;
                                }).join('')}
                                ${availableProviders.length > 3 ? `<span class="text-xs text-blue-600 dark:text-blue-400">+${availableProviders.length - 3}</span>` : ''}
                            </div>
                        ` : `
                            <span class="px-2 py-1 text-xs font-medium rounded ${providerColors[model.provider] || 'bg-gray-100 text-gray-800'}">
                                ${provider.name}
                            </span>
                        `}
                        ${model.status ? `
                            <span class="px-2 py-1 text-xs font-medium rounded ${statusColors[model.status] || 'bg-gray-100 text-gray-800'}">
                                ${statusLabels[model.status] || model.status}
                            </span>
                        ` : ''}
                    </div>
                </div>

                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">${model.name}</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                    ${model.description || '설명이 없습니다.'}
                </p>

                <div class="space-y-3 mb-4">
                    ${this.renderPricing(pricing)}

                    <div class="flex items-center justify-between text-sm">
                        <span class="text-gray-500 dark:text-gray-400">컨텍스트</span>
                        <span class="font-medium text-gray-900 dark:text-white">
                            ${this.formatContextWindow(model.context_window)}
                        </span>
                    </div>
                </div>

                ${model.features && model.features.length > 0 ? `
                    <div class="flex flex-wrap gap-1 mb-4">
                        ${model.features.slice(0, 3).map(feature => `
                            <span class="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                                ${this.getFeatureLabel(feature)}
                            </span>
                        `).join('')}
                        ${model.features.length > 3 ? `
                            <span class="px-2 py-1 text-xs text-gray-500 dark:text-gray-400">
                                +${model.features.length - 3}
                            </span>
                        ` : ''}
                    </div>
                ` : ''}

                <div class="flex gap-2">
                    <button class="btn-compare flex-1 px-3 py-2 text-sm font-medium ${isSelected ? 'bg-blue-500 text-white' : 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'} rounded hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
                            data-model-id="${model.id}" aria-label="${model.name} 모델을 비교 목록에 추가">
                        ${isSelected ? '비교 취소' : '비교하기'}
                    </button>
                    <button class="btn-details flex-1 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                            data-model-id="${model.id}" aria-label="${model.name} 모델 상세 정보 보기">
                        상세보기
                    </button>
                </div>
            </article>
        `;
    }

    renderPricing(pricing) {
        const inputPrice = pricing.input || 0;
        const outputPrice = pricing.output || 0;

        if (inputPrice === 0 && outputPrice === 0) {
            return `
                <div class="flex items-center justify-center py-2 px-3 bg-green-50 dark:bg-green-900/20 rounded">
                    <span class="text-green-700 dark:text-green-400 font-medium">🎉 무료 모델</span>
                </div>
            `;
        }

        return `
            <div class="space-y-2">
                <div class="flex items-center justify-between text-sm">
                    <span class="text-gray-500 dark:text-gray-400">입력 (1M 토큰)</span>
                    <span class="font-medium text-gray-900 dark:text-white">$${inputPrice.toFixed(2)}</span>
                </div>
                <div class="flex items-center justify-between text-sm">
                    <span class="text-gray-500 dark:text-gray-400">출력 (1M 토큰)</span>
                    <span class="font-medium text-gray-900 dark:text-white">$${outputPrice.toFixed(2)}</span>
                </div>
            </div>
        `;
    }

    formatContextWindow(size) {
        if (!size) return 'N/A';

        if (size >= 1000000) {
            return `${(size / 1000000).toFixed(1)}M`;
        } else if (size >= 1000) {
            return `${(size / 1000).toFixed(0)}K`;
        }

        return size.toLocaleString();
    }

    getFeatureLabel(feature) {
        const labels = {
            'chat': '💬 채팅',
            'vision': '👁️ 비전',
            'function-calling': '🔧 함수 호출',
            'json-mode': '📋 JSON',
            'tool-use': '🛠️ 도구 사용',
            'reasoning': '🧠 추론',
            'coding': '💻 코딩',
            'multimodal': '🎨 멀티모달',
            'audio': '🎵 오디오',
            'video': '🎥 비디오',
            'computer-use': '🖥️ 컴퓨터 제어'
        };

        return labels[feature] || feature;
    }

    switchTab(tab) {
        // 탭 버튼 스타일 변경
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        // 탭 컨텐츠 표시/숨김
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });

        const tabContent = document.getElementById(`${tab}-tab`);
        if (tabContent) {
            tabContent.classList.remove('hidden');
        }

        this.currentTab = tab;

        // 탭별 초기화
        switch (tab) {
            case 'comparison':
                this.renderComparison();
                break;
            case 'calculator':
                this.renderCalculator();
                break;
            case 'trends':
                this.renderTrends();
                break;
            case 'providers':
                this.renderProviders();
                break;
        }
    }

    toggleModelComparison(modelId) {
        if (this.selectedModels.has(modelId)) {
            this.selectedModels.delete(modelId);
        } else {
            if (this.selectedModels.size >= 5) {
                this.showNotification('최대 5개까지만 비교할 수 있습니다.', 'warning');
                return;
            }
            this.selectedModels.add(modelId);
        }

        // 버튼 스타일 업데이트
        document.querySelectorAll('.btn-compare').forEach(btn => {
            const btnModelId = btn.getAttribute('data-model-id');
            if (this.selectedModels.has(btnModelId)) {
                btn.textContent = '비교 취소';
                btn.classList.add('bg-blue-500', 'text-white');
                btn.classList.remove('text-blue-600', 'dark:text-blue-400', 'bg-blue-50', 'dark:bg-blue-900/20');
            } else {
                btn.textContent = '비교하기';
                btn.classList.remove('bg-blue-500', 'text-white');
                btn.classList.add('text-blue-600', 'dark:text-blue-400', 'bg-blue-50', 'dark:bg-blue-900/20');
            }
        });

        // Update comparison badge
        this.updateComparisonBadge();

        // If we're currently on the comparison tab, re-render it
        if (this.currentTab === 'comparison') {
            this.renderComparison();
        }

        this.showNotification(`${this.selectedModels.size}개 모델 선택됨`, 'info');
    }

    updateComparisonBadge() {
        const comparisonTab = document.querySelector('[data-tab="comparison"]');
        if (!comparisonTab) return;

        // Remove existing badge
        const existingBadge = comparisonTab.querySelector('.comparison-badge');
        if (existingBadge) {
            existingBadge.remove();
        }

        // Add new badge if there are selected models
        if (this.selectedModels.size > 0) {
            const badge = document.createElement('span');
            badge.className = 'comparison-badge ml-1 px-2 py-0.5 text-xs font-semibold bg-blue-500 text-white rounded-full';
            badge.textContent = this.selectedModels.size;
            badge.setAttribute('aria-label', `${this.selectedModels.size} models selected for comparison`);
            comparisonTab.appendChild(badge);
        }
    }

    showModelDetails(modelId) {
        const model = this.data.models.find(m => m.id === modelId);
        if (!model) return;

        const provider = this.data.providers[model.provider] || { name: model.provider };
        const pricing = model.pricing || {
            input: model.input_price || 0,
            output: model.output_price || 0
        };

        const modal = document.getElementById('modelModal');
        const modalContent = document.getElementById('modalContent');

        if (!modal || !modalContent) return;

        modalContent.innerHTML = `
            <div class="flex items-start justify-between mb-4">
                <div>
                    <h2 id="modalTitle" class="text-2xl font-bold text-gray-900 dark:text-white">${model.name}</h2>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">${provider.name}</p>
                </div>
                <button id="closeModal" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors" aria-label="모달 닫기">
                    <svg class="w-6 h-6 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>

            <div class="space-y-4">
                <div>
                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">설명</h3>
                    <p class="text-gray-600 dark:text-gray-400">${model.description || '설명이 없습니다.'}</p>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">가격 정보</h3>
                        <dl class="space-y-2">
                            <div class="flex justify-between">
                                <dt class="text-sm text-gray-600 dark:text-gray-400">입력 (1M 토큰)</dt>
                                <dd class="text-sm font-medium text-gray-900 dark:text-white">$${pricing.input.toFixed(2)}</dd>
                            </div>
                            <div class="flex justify-between">
                                <dt class="text-sm text-gray-600 dark:text-gray-400">출력 (1M 토큰)</dt>
                                <dd class="text-sm font-medium text-gray-900 dark:text-white">$${pricing.output.toFixed(2)}</dd>
                            </div>
                        </dl>
                    </div>

                    <div>
                        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">사양</h3>
                        <dl class="space-y-2">
                            <div class="flex justify-between">
                                <dt class="text-sm text-gray-600 dark:text-gray-400">컨텍스트 윈도우</dt>
                                <dd class="text-sm font-medium text-gray-900 dark:text-white">${this.formatContextWindow(model.context_window)}</dd>
                            </div>
                            <div class="flex justify-between">
                                <dt class="text-sm text-gray-600 dark:text-gray-400">최대 출력</dt>
                                <dd class="text-sm font-medium text-gray-900 dark:text-white">${model.max_output || 'N/A'}</dd>
                            </div>
                            ${model.release_date ? `
                                <div class="flex justify-between">
                                    <dt class="text-sm text-gray-600 dark:text-gray-400">출시일</dt>
                                    <dd class="text-sm font-medium text-gray-900 dark:text-white">${model.release_date}</dd>
                                </div>
                            ` : ''}
                            ${model.status ? `
                                <div class="flex justify-between">
                                    <dt class="text-sm text-gray-600 dark:text-gray-400">상태</dt>
                                    <dd class="text-sm font-medium text-gray-900 dark:text-white">${model.status.toUpperCase()}</dd>
                                </div>
                            ` : ''}
                        </dl>
                    </div>
                </div>

                ${model.features && model.features.length > 0 ? `
                    <div>
                        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">지원 기능</h3>
                        <div class="flex flex-wrap gap-2">
                            ${model.features.map(feature => `
                                <span class="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-full">
                                    ${this.getFeatureLabel(feature)}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;

        modal.classList.remove('hidden');
        modal.classList.add('flex');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    }

    closeModal() {
        const modal = document.getElementById('modelModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
        }
    }

    renderComparison() {
        const container = document.getElementById('comparisonTable');
        if (!container) return;

        if (this.selectedModels.size === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                    <p>비교할 모델을 선택해주세요.</p>
                    <p class="text-sm mt-2">모델 카드에서 "비교하기" 버튼을 클릭하여 최대 5개까지 선택할 수 있습니다.</p>
                </div>
            `;
            return;
        }

        const selectedModelData = Array.from(this.selectedModels)
            .map(id => this.data.models.find(m => m.id === id))
            .filter(m => m);

        // Calculate min/max for visual comparison aids
        const inputPrices = selectedModelData.map(m => m.pricing?.input || m.input_price || 0);
        const outputPrices = selectedModelData.map(m => m.pricing?.output || m.output_price || 0);
        const contextWindows = selectedModelData.map(m => m.context_window || 0);
        const maxOutputs = selectedModelData.map(m => parseInt(m.max_output) || 0);

        const minInputPrice = Math.min(...inputPrices.filter(p => p > 0));
        const maxInputPrice = Math.max(...inputPrices);
        const minOutputPrice = Math.min(...outputPrices.filter(p => p > 0));
        const maxOutputPrice = Math.max(...outputPrices);
        const maxContext = Math.max(...contextWindows);
        const maxOutput = Math.max(...maxOutputs);

        const statusLabels = {
            ga: 'GA',
            beta: 'Beta',
            preview: 'Preview',
            experimental: 'Experimental',
            deprecated: 'Deprecated'
        };
        const statusColors = {
            ga: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
            beta: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
            preview: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
            experimental: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
            deprecated: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
        };

        container.innerHTML = `
            <!-- Desktop Table View -->
            <div class="comparison-table-container hidden md:block overflow-x-auto">
                <table class="comparison-table w-full" role="table" aria-label="AI Models Comparison">
                    <thead>
                        <tr class="border-b-2 border-gray-300 dark:border-gray-600">
                            <th class="sticky-header text-left py-4 px-4 bg-gray-50 dark:bg-gray-800 font-semibold" scope="col">속성</th>
                            ${selectedModelData.map(model => `
                                <th class="sticky-header text-left py-4 px-4 bg-gray-50 dark:bg-gray-800" scope="col">
                                    <div class="flex items-center justify-between gap-2">
                                        <span class="font-semibold text-gray-900 dark:text-white">${model.name}</span>
                                        <button
                                            class="remove-comparison-btn p-1 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                                            data-model-id="${model.id}"
                                            aria-label="Remove ${model.name} from comparison"
                                            title="Remove from comparison"
                                        >
                                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                            </svg>
                                        </button>
                                    </div>
                                </th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Provider -->
                        <tr class="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                            <td class="py-3 px-4 font-medium text-gray-700 dark:text-gray-300" scope="row">제공업체</td>
                            ${selectedModelData.map(model => `
                                <td class="py-3 px-4 text-gray-900 dark:text-white">${this.data.providers[model.provider]?.name || model.provider}</td>
                            `).join('')}
                        </tr>

                        <!-- Status -->
                        <tr class="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                            <td class="py-3 px-4 font-medium text-gray-700 dark:text-gray-300" scope="row">상태</td>
                            ${selectedModelData.map(model => `
                                <td class="py-3 px-4">
                                    <span class="inline-block px-2 py-1 text-xs font-medium rounded ${statusColors[model.status] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}">
                                        ${statusLabels[model.status] || model.status || 'N/A'}
                                    </span>
                                </td>
                            `).join('')}
                        </tr>

                        <!-- Release Date -->
                        <tr class="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                            <td class="py-3 px-4 font-medium text-gray-700 dark:text-gray-300" scope="row">출시일</td>
                            ${selectedModelData.map(model => `
                                <td class="py-3 px-4 text-gray-900 dark:text-white">${model.release_date || 'N/A'}</td>
                            `).join('')}
                        </tr>

                        <!-- Input Price -->
                        <tr class="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                            <td class="py-3 px-4 font-medium text-gray-700 dark:text-gray-300" scope="row">입력 가격 (1M 토큰)</td>
                            ${selectedModelData.map(model => {
                                const price = model.pricing?.input || model.input_price || 0;
                                const isBest = price === minInputPrice && price > 0;
                                const percentage = maxInputPrice > 0 ? (price / maxInputPrice) * 100 : 0;
                                return `
                                    <td class="py-3 px-4">
                                        <div class="space-y-1">
                                            <div class="flex items-center justify-between">
                                                <span class="font-medium ${isBest ? 'text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-white'}">
                                                    $${price.toFixed(2)}
                                                </span>
                                                ${isBest ? '<span class="text-xs text-green-600 dark:text-green-400 font-medium">최저가</span>' : ''}
                                            </div>
                                            <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                                <div class="h-full ${isBest ? 'bg-green-500' : 'bg-blue-500'} rounded-full transition-all duration-300" style="width: ${percentage}%"></div>
                                            </div>
                                        </div>
                                    </td>
                                `;
                            }).join('')}
                        </tr>

                        <!-- Output Price -->
                        <tr class="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                            <td class="py-3 px-4 font-medium text-gray-700 dark:text-gray-300" scope="row">출력 가격 (1M 토큰)</td>
                            ${selectedModelData.map(model => {
                                const price = model.pricing?.output || model.output_price || 0;
                                const isBest = price === minOutputPrice && price > 0;
                                const percentage = maxOutputPrice > 0 ? (price / maxOutputPrice) * 100 : 0;
                                return `
                                    <td class="py-3 px-4">
                                        <div class="space-y-1">
                                            <div class="flex items-center justify-between">
                                                <span class="font-medium ${isBest ? 'text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-white'}">
                                                    $${price.toFixed(2)}
                                                </span>
                                                ${isBest ? '<span class="text-xs text-green-600 dark:text-green-400 font-medium">최저가</span>' : ''}
                                            </div>
                                            <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                                <div class="h-full ${isBest ? 'bg-green-500' : 'bg-blue-500'} rounded-full transition-all duration-300" style="width: ${percentage}%"></div>
                                            </div>
                                        </div>
                                    </td>
                                `;
                            }).join('')}
                        </tr>

                        <!-- Context Window -->
                        <tr class="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                            <td class="py-3 px-4 font-medium text-gray-700 dark:text-gray-300" scope="row">컨텍스트 윈도우</td>
                            ${selectedModelData.map(model => {
                                const context = model.context_window || 0;
                                const isBest = context === maxContext && context > 0;
                                const percentage = maxContext > 0 ? (context / maxContext) * 100 : 0;
                                return `
                                    <td class="py-3 px-4">
                                        <div class="space-y-1">
                                            <div class="flex items-center justify-between">
                                                <span class="font-medium ${isBest ? 'text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-white'}">
                                                    ${this.formatContextWindow(context)}
                                                </span>
                                                ${isBest ? '<span class="text-xs text-green-600 dark:text-green-400 font-medium">최대</span>' : ''}
                                            </div>
                                            <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                                <div class="h-full ${isBest ? 'bg-green-500' : 'bg-blue-500'} rounded-full transition-all duration-300" style="width: ${percentage}%"></div>
                                            </div>
                                        </div>
                                    </td>
                                `;
                            }).join('')}
                        </tr>

                        <!-- Max Output -->
                        <tr class="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                            <td class="py-3 px-4 font-medium text-gray-700 dark:text-gray-300" scope="row">최대 출력 토큰</td>
                            ${selectedModelData.map(model => {
                                const output = parseInt(model.max_output) || 0;
                                const isBest = output === maxOutput && output > 0;
                                const percentage = maxOutput > 0 ? (output / maxOutput) * 100 : 0;
                                return `
                                    <td class="py-3 px-4">
                                        <div class="space-y-1">
                                            <div class="flex items-center justify-between">
                                                <span class="font-medium ${isBest ? 'text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-white'}">
                                                    ${output > 0 ? this.formatContextWindow(output) : 'N/A'}
                                                </span>
                                                ${isBest ? '<span class="text-xs text-green-600 dark:text-green-400 font-medium">최대</span>' : ''}
                                            </div>
                                            ${output > 0 ? `
                                                <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                                    <div class="h-full ${isBest ? 'bg-green-500' : 'bg-blue-500'} rounded-full transition-all duration-300" style="width: ${percentage}%"></div>
                                                </div>
                                            ` : ''}
                                        </div>
                                    </td>
                                `;
                            }).join('')}
                        </tr>

                        <!-- Features -->
                        <tr class="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                            <td class="py-3 px-4 font-medium text-gray-700 dark:text-gray-300" scope="row">주요 기능</td>
                            ${selectedModelData.map(model => `
                                <td class="py-3 px-4">
                                    <div class="flex flex-wrap gap-1">
                                        ${(model.features || []).map(feature => `
                                            <span class="px-2 py-1 text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded">
                                                ${this.getFeatureLabel(feature)}
                                            </span>
                                        `).join('')}
                                        ${(model.features || []).length === 0 ? '<span class="text-gray-500 dark:text-gray-400 text-sm">N/A</span>' : ''}
                                    </div>
                                </td>
                            `).join('')}
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Mobile Card View -->
            <div class="comparison-cards-container md:hidden space-y-4">
                ${selectedModelData.map(model => {
                    const inputPrice = model.pricing?.input || model.input_price || 0;
                    const outputPrice = model.pricing?.output || model.output_price || 0;
                    const context = model.context_window || 0;
                    const output = parseInt(model.max_output) || 0;

                    const inputBest = inputPrice === minInputPrice && inputPrice > 0;
                    const outputBest = outputPrice === minOutputPrice && outputPrice > 0;
                    const contextBest = context === maxContext && context > 0;
                    const outputBest2 = output === maxOutput && output > 0;

                    return `
                        <div class="comparison-card bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4" role="article" aria-label="${model.name} comparison details">
                            <div class="flex items-start justify-between mb-4">
                                <div>
                                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">${model.name}</h3>
                                    <p class="text-sm text-gray-600 dark:text-gray-400">${this.data.providers[model.provider]?.name || model.provider}</p>
                                </div>
                                <button
                                    class="remove-comparison-btn p-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                                    data-model-id="${model.id}"
                                    aria-label="Remove ${model.name} from comparison"
                                >
                                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                    </svg>
                                </button>
                            </div>

                            <div class="space-y-3">
                                <div>
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="text-sm text-gray-600 dark:text-gray-400">상태</span>
                                        <span class="px-2 py-1 text-xs font-medium rounded ${statusColors[model.status] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}">
                                            ${statusLabels[model.status] || model.status || 'N/A'}
                                        </span>
                                    </div>
                                </div>

                                <div>
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="text-sm text-gray-600 dark:text-gray-400">출시일</span>
                                        <span class="text-sm font-medium text-gray-900 dark:text-white">${model.release_date || 'N/A'}</span>
                                    </div>
                                </div>

                                <div>
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="text-sm text-gray-600 dark:text-gray-400">입력 가격</span>
                                        <span class="text-sm font-medium ${inputBest ? 'text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-white'}">
                                            $${inputPrice.toFixed(2)} ${inputBest ? '(최저가)' : ''}
                                        </span>
                                    </div>
                                    <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                        <div class="h-full ${inputBest ? 'bg-green-500' : 'bg-blue-500'} rounded-full transition-all duration-300" style="width: ${maxInputPrice > 0 ? (inputPrice / maxInputPrice) * 100 : 0}%"></div>
                                    </div>
                                </div>

                                <div>
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="text-sm text-gray-600 dark:text-gray-400">출력 가격</span>
                                        <span class="text-sm font-medium ${outputBest ? 'text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-white'}">
                                            $${outputPrice.toFixed(2)} ${outputBest ? '(최저가)' : ''}
                                        </span>
                                    </div>
                                    <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                        <div class="h-full ${outputBest ? 'bg-green-500' : 'bg-blue-500'} rounded-full transition-all duration-300" style="width: ${maxOutputPrice > 0 ? (outputPrice / maxOutputPrice) * 100 : 0}%"></div>
                                    </div>
                                </div>

                                <div>
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="text-sm text-gray-600 dark:text-gray-400">컨텍스트</span>
                                        <span class="text-sm font-medium ${contextBest ? 'text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-white'}">
                                            ${this.formatContextWindow(context)} ${contextBest ? '(최대)' : ''}
                                        </span>
                                    </div>
                                    <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                        <div class="h-full ${contextBest ? 'bg-green-500' : 'bg-blue-500'} rounded-full transition-all duration-300" style="width: ${maxContext > 0 ? (context / maxContext) * 100 : 0}%"></div>
                                    </div>
                                </div>

                                <div>
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="text-sm text-gray-600 dark:text-gray-400">최대 출력</span>
                                        <span class="text-sm font-medium ${outputBest2 ? 'text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-white'}">
                                            ${output > 0 ? this.formatContextWindow(output) : 'N/A'} ${outputBest2 ? '(최대)' : ''}
                                        </span>
                                    </div>
                                    ${output > 0 ? `
                                        <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                            <div class="h-full ${outputBest2 ? 'bg-green-500' : 'bg-blue-500'} rounded-full transition-all duration-300" style="width: ${maxOutput > 0 ? (output / maxOutput) * 100 : 0}%"></div>
                                        </div>
                                    ` : ''}
                                </div>

                                <div>
                                    <div class="mb-1">
                                        <span class="text-sm text-gray-600 dark:text-gray-400">주요 기능</span>
                                    </div>
                                    <div class="flex flex-wrap gap-1">
                                        ${(model.features || []).map(feature => `
                                            <span class="px-2 py-1 text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded">
                                                ${this.getFeatureLabel(feature)}
                                            </span>
                                        `).join('')}
                                        ${(model.features || []).length === 0 ? '<span class="text-gray-500 dark:text-gray-400 text-sm">N/A</span>' : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        // Add event listeners for remove buttons
        container.querySelectorAll('.remove-comparison-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modelId = btn.getAttribute('data-model-id');
                this.toggleModelComparison(modelId);
            });
        });
    }

    renderCalculator() {
        const container = document.getElementById('priceCalculator');
        if (!container) return;

        // 가격 계산기는 별도 컴포넌트로 구현
        const script = document.createElement('script');
        script.type = 'module';
        script.textContent = `
            import { PriceCalculator } from './src/js/price-calculator.js';
            new PriceCalculator(window.dashboard);
        `;
        document.body.appendChild(script);
    }

    renderTrends() {
        // 차트는 별도 컴포넌트로 구현
        const script = document.createElement('script');
        script.type = 'module';
        script.textContent = `
            import { ChartsManager } from './src/js/charts.js';
            new ChartsManager(window.dashboard);
        `;
        document.body.appendChild(script);
    }

    renderProviders() {
        const providersView = document.getElementById('providersView');
        if (!providersView) return;

        const providerColors = {
            openai: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 border-green-300',
            anthropic: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 border-orange-300',
            google: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-blue-300',
            deepseek: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200 border-indigo-300',
            xai: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200 border-cyan-300',
            mistral: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200 border-pink-300',
            cohere: 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200 border-teal-300',
            huggingface: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 border-yellow-300',
            meta: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-blue-300'
        };

        const providers = Object.keys(this.data.providers).filter(p => p !== 'openrouter');

        providersView.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                ${providers.map(providerKey => {
                    const provider = this.data.providers[providerKey];
                    const providerModels = this.data.models.filter(m => m.provider === providerKey);

                    // 가격 범위 계산
                    const prices = providerModels
                        .map(m => m.pricing?.input || 0)
                        .filter(p => p > 0);
                    const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
                    const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;

                    return `
                        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border-2 ${providerColors[providerKey]?.split(' ').pop() || 'border-gray-300'} p-6 hover:shadow-md transition-shadow">
                            <div class="flex items-center justify-between mb-4">
                                <h3 class="text-xl font-bold text-gray-900 dark:text-white">${provider.name}</h3>
                                <span class="px-3 py-1 text-sm font-medium rounded ${providerColors[providerKey] || 'bg-gray-100 text-gray-800'}">
                                    ${provider.model_count} 모델
                                </span>
                            </div>

                            <div class="space-y-3 mb-4">
                                <div class="flex items-center justify-between text-sm">
                                    <span class="text-gray-500 dark:text-gray-400">웹사이트</span>
                                    <a href="${provider.website}" target="_blank" class="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 flex items-center gap-1">
                                        <span>방문</span>
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                                        </svg>
                                    </a>
                                </div>

                                ${prices.length > 0 ? `
                                    <div class="flex items-center justify-between text-sm">
                                        <span class="text-gray-500 dark:text-gray-400">가격 범위</span>
                                        <span class="font-medium text-gray-900 dark:text-white">
                                            $${minPrice.toFixed(2)} - $${maxPrice.toFixed(2)}
                                        </span>
                                    </div>
                                ` : ''}

                                <div class="flex items-center justify-between text-sm">
                                    <span class="text-gray-500 dark:text-gray-400">마지막 업데이트</span>
                                    <span class="text-gray-700 dark:text-gray-300">
                                        ${new Date(provider.last_updated).toLocaleDateString('ko-KR')}
                                    </span>
                                </div>
                            </div>

                            <button
                                class="filter-btn w-full px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                                data-filter="${providerKey}"
                            >
                                모델 보기
                            </button>

                            <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                                <h4 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">주요 모델</h4>
                                <ul class="space-y-1">
                                    ${providerModels.slice(0, 3).map(m => `
                                        <li class="text-xs text-gray-600 dark:text-gray-400 truncate">
                                            • ${m.name}
                                        </li>
                                    `).join('')}
                                    ${providerModels.length > 3 ? `
                                        <li class="text-xs text-gray-500 dark:text-gray-500">
                                            ... 외 ${providerModels.length - 3}개
                                        </li>
                                    ` : ''}
                                </ul>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        // 필터 버튼 이벤트 리스너는 이미 설정되어 있음
        // "모델 보기" 버튼을 누르면 models 탭으로 이동하고 해당 제공업체 필터 적용
        providersView.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.switchTab('models');
                this.handleFilterClick(btn);
            });
        });
    }

    applyTheme() {
        const theme = localStorage.getItem('theme') || 'light';
        document.documentElement.classList.toggle('dark', theme === 'dark');
    }

    toggleTheme() {
        const isDark = document.documentElement.classList.contains('dark');
        const newTheme = isDark ? 'light' : 'dark';

        document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', newTheme);
    }

    setupAutoRefresh() {
        // 5분마다 데이터 새로고침 확인
        setInterval(async () => {
            try {
                const response = await fetch('./data/consolidated.json');
                const newData = await response.json();

                if (newData.last_updated !== this.data.last_updated) {
                    this.showUpdateNotification();
                }
            } catch (error) {
                console.error('Auto-refresh failed:', error);
            }
        }, 5 * 60 * 1000);
    }

    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'fixed top-20 right-4 bg-blue-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-3 z-50';
        notification.innerHTML = `
            <span>🔄 새로운 데이터가 업데이트되었습니다!</span>
            <button onclick="location.reload()" class="px-3 py-1 bg-white text-blue-500 rounded hover:bg-blue-50 transition-colors">
                새로고침
            </button>
        `;

        document.body.appendChild(notification);

        // 10초 후 자동 제거
        setTimeout(() => notification.remove(), 10000);
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        if (!container) return;

        const notification = document.createElement('div');
        const typeStyles = {
            info: 'bg-blue-500',
            success: 'bg-green-500',
            warning: 'bg-yellow-500',
            error: 'bg-red-500'
        };

        notification.className = `${typeStyles[type]} text-white px-4 py-2 rounded-lg shadow-lg mb-2 transition-opacity`;
        notification.textContent = message;

        container.appendChild(notification);

        // 3초 후 제거
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    showError(message) {
        this.showNotification(message, 'error');
    }
}

// CSS 스타일 추가 (line-clamp utility)
const style = document.createElement('style');
style.textContent = `
    .line-clamp-2 {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
`;
document.head.appendChild(style);

// 애플리케이션 시작
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new AIModelsDashboard();
});
