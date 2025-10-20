// Main Application Class
class AIModelsDashboard {
    constructor() {
        this.data = null;
        this.filteredModels = [];
        this.currentFilter = 'all';
        this.searchTerm = '';
        this.currentTab = 'models';
        this.selectedModels = new Set();
        
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
        // 검색
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchTerm = e.target.value.toLowerCase();
                this.applyFilters();
            });
        }
        
        // 필터 버튼 클릭
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('filter-btn')) {
                this.handleFilterClick(e.target);
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
        this.applyFilters();
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
        this.renderModels();
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
            modelsGrid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">검색 결과가 없습니다</h3>
                    <p class="text-gray-600 dark:text-gray-400">다른 검색어나 필터를 시도해보세요.</p>
                </div>
            `;
            return;
        }
        
        modelsGrid.innerHTML = this.filteredModels.map(model => 
            this.createModelCard(model)
        ).join('');
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
        
        // 제공업체 링크 생성 함수
        const getProviderLink = (providerName) => {
            const pInfo = this.data.providers[providerName] || {};
            return pInfo.platform_url || pInfo.website || '#';
        };
        
        return `
            <div class="model-card bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex flex-wrap items-center gap-2">
                        ${hasMultipleProviders ? `
                            <div class="flex items-center gap-1 px-2 py-1 bg-blue-50 dark:bg-blue-900/20 rounded">
                                <span class="text-xs font-medium text-blue-700 dark:text-blue-300">다중 제공업체:</span>
                                ${availableProviders.slice(0, 3).map(p => {
                                    const pInfo = this.data.providers[p] || { name: p };
                                    const providerLink = getProviderLink(p);
                                    return `<a href="${providerLink}" target="_blank" rel="noopener noreferrer" 
                                            class="px-1.5 py-0.5 text-xs font-medium rounded ${providerColors[p] || 'bg-gray-100 text-gray-800'} hover:opacity-80 transition-opacity" 
                                            title="${pInfo.name}에서 사용하기">${pInfo.name}</a>`;
                                }).join('')}
                                ${availableProviders.length > 3 ? `<span class="text-xs text-blue-600 dark:text-blue-400">+${availableProviders.length - 3}</span>` : ''}
                            </div>
                        ` : `
                            <a href="${getProviderLink(model.provider)}" target="_blank" rel="noopener noreferrer" 
                               class="px-2 py-1 text-xs font-medium rounded ${providerColors[model.provider] || 'bg-gray-100 text-gray-800'} hover:opacity-80 transition-opacity inline-block" 
                               title="${provider.name}에서 사용하기">
                                ${provider.name}
                            </a>
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
                    <button class="btn-compare flex-1 px-3 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 rounded hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors" 
                            data-model-id="${model.id}">
                        비교하기
                    </button>
                    <button class="btn-details flex-1 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors" 
                            data-model-id="${model.id}">
                        상세보기
                    </button>
                </div>
            </div>
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
                btn.classList.remove('text-blue-600', 'bg-blue-50');
            } else {
                btn.textContent = '비교하기';
                btn.classList.remove('bg-blue-500', 'text-white');
                btn.classList.add('text-blue-600', 'bg-blue-50');
            }
        });
        
        this.showNotification(`${this.selectedModels.size}개 모델 선택됨`, 'info');
    }
    
    showModelDetails(modelId) {
        const model = this.data.models.find(m => m.id === modelId);
        if (!model) return;
        
        // 상세 정보 모달 표시 (간단한 alert로 대체)
        const details = `
${model.name} (${model.provider})

${model.description}

가격:
- 입력: $${(model.pricing?.input || model.input_price || 0).toFixed(2)}/1M tokens
- 출력: $${(model.pricing?.output || model.output_price || 0).toFixed(2)}/1M tokens

컨텍스트: ${this.formatContextWindow(model.context_window)}
최대 출력: ${model.max_output || 'N/A'}
출시일: ${model.release_date || 'N/A'}
상태: ${model.status || 'N/A'}

기능: ${(model.features || []).join(', ')}
        `.trim();
        
        alert(details);
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
        
        container.innerHTML = `
            <table class="w-full">
                <thead>
                    <tr class="border-b dark:border-gray-700">
                        <th class="text-left py-3 px-4">속성</th>
                        ${selectedModelData.map(model => `
                            <th class="text-left py-3 px-4">${model.name}</th>
                        `).join('')}
                    </tr>
                </thead>
                <tbody>
                    <tr class="border-b dark:border-gray-700">
                        <td class="py-3 px-4 font-medium">제공업체</td>
                        ${selectedModelData.map(model => `
                            <td class="py-3 px-4">${this.data.providers[model.provider]?.name || model.provider}</td>
                        `).join('')}
                    </tr>
                    <tr class="border-b dark:border-gray-700">
                        <td class="py-3 px-4 font-medium">입력 가격</td>
                        ${selectedModelData.map(model => `
                            <td class="py-3 px-4">$${(model.pricing?.input || model.input_price || 0).toFixed(2)}</td>
                        `).join('')}
                    </tr>
                    <tr class="border-b dark:border-gray-700">
                        <td class="py-3 px-4 font-medium">출력 가격</td>
                        ${selectedModelData.map(model => `
                            <td class="py-3 px-4">$${(model.pricing?.output || model.output_price || 0).toFixed(2)}</td>
                        `).join('')}
                    </tr>
                    <tr class="border-b dark:border-gray-700">
                        <td class="py-3 px-4 font-medium">컨텍스트</td>
                        ${selectedModelData.map(model => `
                            <td class="py-3 px-4">${this.formatContextWindow(model.context_window)}</td>
                        `).join('')}
                    </tr>
                </tbody>
            </table>
        `;
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
        notification.className = 'fixed top-20 right-4 bg-blue-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-3';
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

// CSS 스타일 추가
const style = document.createElement('style');
style.textContent = `
    .tab-button {
        @apply px-4 py-2 font-medium text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white border-b-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600 flex items-center transition-colors;
    }
    
    .tab-button.active {
        @apply text-blue-600 dark:text-blue-400 border-blue-500;
    }
    
    .line-clamp-2 {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    .model-card {
        animation: fadeIn 0.3s ease-in-out;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);

// 애플리케이션 시작
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new AIModelsDashboard();
});