export class ChartsManager {
    // Singleton instance
    static instance = null;

    // Cache for history data
    static dataCache = {
        historyData: null,
        timestamp: null,
        cacheDuration: 5 * 60 * 1000 // 5 minutes
    };

    constructor(dashboard) {
        // Implement singleton pattern to prevent memory leaks
        if (ChartsManager.instance) {
            return ChartsManager.instance;
        }

        this.dashboard = dashboard;
        this.charts = {};
        this.selectedModels = new Set([
            'gpt-4o',
            'claude-3-5-sonnet',
            'gemini-1-5-pro',
            'gpt-4o-mini',
            'claude-3-5-haiku'
        ]);

        ChartsManager.instance = this;
        this.init();
    }

    static getInstance(dashboard) {
        if (!ChartsManager.instance) {
            ChartsManager.instance = new ChartsManager(dashboard);
        }
        return ChartsManager.instance;
    }

    async init() {
        await this.renderPriceHistory();
    }

    async renderPriceHistory() {
        const container = document.getElementById('trends-tab');
        if (!container) return;

        try {
            // Show loading state
            this.showLoadingState(container);

            // Load history data with caching
            const historyData = await this.loadHistoryDataWithCache(30);

            if (historyData.length > 0) {
                this.createPriceHistoryChart(historyData);
            } else {
                // Use sample data if no history available
                this.createSampleChart();
            }
        } catch (error) {
            console.error('Failed to render price history:', error);
            this.showErrorState(container, error);
        }
    }

    showLoadingState(container) {
        const chartContainer = container.querySelector('.bg-white');
        if (!chartContainer) return;

        const canvasContainer = chartContainer.querySelector('div:last-child');
        if (!canvasContainer) return;

        canvasContainer.innerHTML = `
            <div class="flex items-center justify-center h-full min-h-[400px]" role="status" aria-live="polite" aria-label="Loading price trends data">
                <div class="text-center">
                    <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-blue-600 dark:border-gray-600 dark:border-t-blue-400"></div>
                    <p class="mt-4 text-gray-600 dark:text-gray-400">가격 트렌드 데이터를 불러오는 중...</p>
                </div>
            </div>
        `;
    }

    showErrorState(container, error) {
        const chartContainer = container.querySelector('.bg-white');
        if (!chartContainer) return;

        const canvasContainer = chartContainer.querySelector('div:last-child');
        if (!canvasContainer) return;

        canvasContainer.innerHTML = `
            <div class="flex items-center justify-center h-full min-h-[400px]" role="alert" aria-live="assertive">
                <div class="text-center max-w-md">
                    <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/20 mb-4">
                        <svg class="h-6 w-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">데이터를 불러올 수 없습니다</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">${error.message || '알 수 없는 오류가 발생했습니다.'}</p>
                    <button
                        onclick="window.dashboard.chartsManager?.renderPriceHistory()"
                        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                        다시 시도
                    </button>
                </div>
            </div>
        `;
    }

    async loadHistoryDataWithCache(days) {
        const now = Date.now();
        const cache = ChartsManager.dataCache;

        // Return cached data if still valid
        if (cache.historyData && cache.timestamp && (now - cache.timestamp) < cache.cacheDuration) {
            console.log('Using cached history data');
            return cache.historyData;
        }

        // Load fresh data
        const historyData = await this.loadHistoryData(days);

        // Update cache
        cache.historyData = historyData;
        cache.timestamp = now;

        return historyData;
    }

    async loadHistoryData(days) {
        const promises = [];
        const today = new Date();

        for (let i = 0; i < days; i++) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];

            promises.push(
                fetch(`./data/history/${dateStr}.json`)
                    .then(res => res.ok ? res.json() : null)
                    .catch(() => null)
            );
        }

        const results = await Promise.all(promises);
        return results.filter(data => data !== null).reverse();
    }
    
    createPriceHistoryChart(historyData) {
        const canvas = document.getElementById('priceHistoryChart');
        if (!canvas) return;

        // Add ARIA labels to canvas for accessibility
        canvas.setAttribute('role', 'img');
        canvas.setAttribute('aria-label', 'Price trends chart showing historical pricing data for AI models');

        const container = canvas.parentElement;
        if (container) {
            container.setAttribute('role', 'region');
            container.setAttribute('aria-label', 'Price trends visualization');
        }

        // Render model selection UI before chart
        this.renderModelSelectionUI(historyData);

        const ctx = canvas.getContext('2d');

        // Available models to track
        const trackedModels = [
            { id: 'gpt-4o', name: 'GPT-4o', color: '#10a37f' },
            { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', color: '#d2691e' },
            { id: 'gemini-1-5-pro', name: 'Gemini 1.5 Pro', color: '#4285f4' },
            { id: 'gpt-4o-mini', name: 'GPT-4o mini', color: '#22c55e' },
            { id: 'claude-3-5-haiku', name: 'Claude 3.5 Haiku', color: '#f97316' }
        ];

        // Filter datasets based on selected models
        const datasets = trackedModels
            .filter(modelInfo => this.selectedModels.has(modelInfo.id))
            .map(modelInfo => {
                const data = historyData.map(day => {
                    const model = day.price_snapshot?.find(m =>
                        m.id === modelInfo.id ||
                        m.unique_id === `openai/${modelInfo.id}` ||
                        m.unique_id === `anthropic/${modelInfo.id}` ||
                        m.unique_id === `google/${modelInfo.id}`
                    );

                    return {
                        x: day.date,
                        y: model ? model.input_price : null
                    };
                }).filter(point => point.y !== null);

                return {
                    label: modelInfo.name,
                    data: data,
                    borderColor: modelInfo.color,
                    backgroundColor: modelInfo.color + '20',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    tension: 0.1,
                    fill: false
                };
            }).filter(dataset => dataset.data.length > 0);
        
        // 기존 차트가 있으면 제거
        if (this.charts.priceHistory) {
            this.charts.priceHistory.destroy();
        }
        
        this.charts.priceHistory = new Chart(ctx, {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'MM/dd'
                            }
                        },
                        title: {
                            display: true,
                            text: '날짜',
                            font: {
                                size: 14
                            }
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '입력 가격 ($/1M tokens)',
                            font: {
                                size: 14
                            }
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: '주요 모델 가격 변화 추이',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        padding: {
                            bottom: 20
                        }
                    },
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += '$' + context.parsed.y.toFixed(2) + '/1M tokens';
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }
    
    renderModelSelectionUI(historyData) {
        const container = document.getElementById('trends-tab');
        if (!container) return;

        const chartContainer = container.querySelector('.bg-white');
        if (!chartContainer) return;

        // Check if model selection UI already exists
        let selectionUI = chartContainer.querySelector('.model-selection-ui');
        if (!selectionUI) {
            const heading = chartContainer.querySelector('h3');
            selectionUI = document.createElement('div');
            selectionUI.className = 'model-selection-ui mb-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg';
            heading.insertAdjacentElement('afterend', selectionUI);
        }

        const trackedModels = [
            { id: 'gpt-4o', name: 'GPT-4o', color: '#10a37f' },
            { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', color: '#d2691e' },
            { id: 'gemini-1-5-pro', name: 'Gemini 1.5 Pro', color: '#4285f4' },
            { id: 'gpt-4o-mini', name: 'GPT-4o mini', color: '#22c55e' },
            { id: 'claude-3-5-haiku', name: 'Claude 3.5 Haiku', color: '#f97316' }
        ];

        selectionUI.innerHTML = `
            <div class="flex items-center justify-between flex-wrap gap-3">
                <div>
                    <h4 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">표시할 모델 선택</h4>
                    <p class="text-xs text-gray-600 dark:text-gray-400">모델을 클릭하여 차트에서 표시/숨김을 전환하세요</p>
                </div>
                <div class="flex flex-wrap gap-2" role="group" aria-label="Model selection toggles">
                    ${trackedModels.map(model => `
                        <button
                            class="model-toggle-btn px-3 py-1.5 text-sm font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                                this.selectedModels.has(model.id)
                                    ? 'text-white shadow-sm'
                                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-2 border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                            }"
                            data-model-id="${model.id}"
                            style="${this.selectedModels.has(model.id) ? `background-color: ${model.color}; border-color: ${model.color};` : ''}"
                            aria-pressed="${this.selectedModels.has(model.id)}"
                            title="Toggle ${model.name}"
                        >
                            ${model.name}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;

        // Attach event listeners
        selectionUI.querySelectorAll('.model-toggle-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modelId = btn.getAttribute('data-model-id');
                this.toggleModel(modelId, historyData);
            });
        });
    }

    toggleModel(modelId, historyData) {
        if (this.selectedModels.has(modelId)) {
            this.selectedModels.delete(modelId);
        } else {
            this.selectedModels.add(modelId);
        }

        // Re-render the chart with updated selection
        this.createPriceHistoryChart(historyData);
    }

    createSampleChart() {
        const canvas = document.getElementById('priceHistoryChart');
        if (!canvas) return;

        // Add ARIA labels
        canvas.setAttribute('role', 'img');
        canvas.setAttribute('aria-label', 'Sample price trends chart showing simulated pricing data for AI models');

        const container = canvas.parentElement;
        if (container) {
            container.setAttribute('role', 'region');
            container.setAttribute('aria-label', 'Sample price trends visualization');
        }

        const ctx = canvas.getContext('2d');

        // Generate sample data (last 30 days)
        const days = 30;
        const today = new Date();
        const dates = [];

        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            dates.push(date.toISOString().split('T')[0]);
        }

        // Sample price data
        const models = [
            {
                id: 'gpt-4o',
                label: 'GPT-4o',
                color: '#10a37f',
                basePrice: 2.50,
                variance: 0.1
            },
            {
                id: 'claude-3-5-sonnet',
                label: 'Claude 3.5 Sonnet',
                color: '#d2691e',
                basePrice: 3.00,
                variance: 0.15
            },
            {
                id: 'gemini-1-5-pro',
                label: 'Gemini 1.5 Pro',
                color: '#4285f4',
                basePrice: 1.25,
                variance: 0.08
            }
        ];

        // Render model selection UI for sample data
        this.renderModelSelectionUIForSample();

        const datasets = models
            .filter(model => this.selectedModels.has(model.id))
            .map(model => {
                const data = dates.map((date, index) => {
                    // Simulate price fluctuations
                    let price = model.basePrice;
                    if (index > 20) {
                        // Small price changes in the last 10 days
                        price += (Math.random() - 0.5) * model.variance;
                    }

                    return {
                        x: date,
                        y: Math.max(0, price)
                    };
                });

                return {
                    label: model.label,
                    data: data,
                    borderColor: model.color,
                    backgroundColor: model.color + '20',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    tension: 0.1,
                    fill: false
                };
            });
        
        // 기존 차트가 있으면 제거
        if (this.charts.priceHistory) {
            this.charts.priceHistory.destroy();
        }
        
        this.charts.priceHistory = new Chart(ctx, {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'MM/dd'
                            }
                        },
                        title: {
                            display: true,
                            text: '날짜'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '입력 가격 ($/1M tokens)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: '주요 모델 가격 변화 추이 (샘플 데이터)',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + context.parsed.y.toFixed(2) + '/1M tokens';
                            }
                        }
                    }
                }
            }
        });
        
        // Sample data notice
        const canvasContainer = canvas.parentElement;
        if (canvasContainer && !canvasContainer.querySelector('.sample-data-notice')) {
            const notice = document.createElement('div');
            notice.className = 'sample-data-notice mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg text-sm text-yellow-800 dark:text-yellow-200';
            notice.innerHTML = `
                <div class="flex items-center gap-2">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                    </svg>
                    <span>현재 샘플 데이터를 표시하고 있습니다. 실제 데이터는 GitHub Actions를 통해 수집됩니다.</span>
                </div>
            `;
            canvasContainer.appendChild(notice);
        }
    }

    renderModelSelectionUIForSample() {
        const container = document.getElementById('trends-tab');
        if (!container) return;

        const chartContainer = container.querySelector('.bg-white');
        if (!chartContainer) return;

        // Check if model selection UI already exists
        let selectionUI = chartContainer.querySelector('.model-selection-ui');
        if (!selectionUI) {
            const heading = chartContainer.querySelector('h3');
            selectionUI = document.createElement('div');
            selectionUI.className = 'model-selection-ui mb-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg';
            heading.insertAdjacentElement('afterend', selectionUI);
        }

        const trackedModels = [
            { id: 'gpt-4o', name: 'GPT-4o', color: '#10a37f' },
            { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', color: '#d2691e' },
            { id: 'gemini-1-5-pro', name: 'Gemini 1.5 Pro', color: '#4285f4' }
        ];

        selectionUI.innerHTML = `
            <div class="flex items-center justify-between flex-wrap gap-3">
                <div>
                    <h4 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">표시할 모델 선택</h4>
                    <p class="text-xs text-gray-600 dark:text-gray-400">모델을 클릭하여 차트에서 표시/숨김을 전환하세요</p>
                </div>
                <div class="flex flex-wrap gap-2" role="group" aria-label="Model selection toggles">
                    ${trackedModels.map(model => `
                        <button
                            class="model-toggle-btn px-3 py-1.5 text-sm font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                                this.selectedModels.has(model.id)
                                    ? 'text-white shadow-sm'
                                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-2 border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                            }"
                            data-model-id="${model.id}"
                            style="${this.selectedModels.has(model.id) ? `background-color: ${model.color}; border-color: ${model.color};` : ''}"
                            aria-pressed="${this.selectedModels.has(model.id)}"
                            title="Toggle ${model.name}"
                        >
                            ${model.name}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;

        // Attach event listeners
        selectionUI.querySelectorAll('.model-toggle-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const modelId = btn.getAttribute('data-model-id');
                this.toggleModelSample(modelId);
            });
        });
    }

    toggleModelSample(modelId) {
        if (this.selectedModels.has(modelId)) {
            this.selectedModels.delete(modelId);
        } else {
            this.selectedModels.add(modelId);
        }

        // Re-render the sample chart with updated selection
        this.createSampleChart();
    }

    destroy() {
        // Clean up all charts
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = {};

        // Clear singleton instance
        ChartsManager.instance = null;
    }
}