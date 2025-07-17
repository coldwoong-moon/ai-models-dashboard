export class ChartsManager {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.charts = {};
        this.init();
    }
    
    async init() {
        await this.renderPriceHistory();
    }
    
    async renderPriceHistory() {
        try {
            // 최근 30일 히스토리 데이터 로드
            const historyData = await this.loadHistoryData(30);
            if (historyData.length > 0) {
                this.createPriceHistoryChart(historyData);
            } else {
                // 히스토리 데이터가 없으면 샘플 데이터로 차트 생성
                this.createSampleChart();
            }
        } catch (error) {
            console.error('Failed to render price history:', error);
            this.createSampleChart();
        }
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
        
        const ctx = canvas.getContext('2d');
        
        // 추적할 주요 모델들
        const trackedModels = [
            { id: 'gpt-4o', name: 'GPT-4o', color: '#10a37f' },
            { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', color: '#d2691e' },
            { id: 'gemini-1-5-pro', name: 'Gemini 1.5 Pro', color: '#4285f4' },
            { id: 'gpt-4o-mini', name: 'GPT-4o mini', color: '#22c55e' },
            { id: 'claude-3-5-haiku', name: 'Claude 3.5 Haiku', color: '#f97316' }
        ];
        
        const datasets = trackedModels.map(modelInfo => {
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
    
    createSampleChart() {
        const canvas = document.getElementById('priceHistoryChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // 샘플 데이터 생성 (최근 30일)
        const days = 30;
        const today = new Date();
        const dates = [];
        
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            dates.push(date.toISOString().split('T')[0]);
        }
        
        // 샘플 가격 데이터
        const models = [
            {
                label: 'GPT-4o',
                color: '#10a37f',
                basePrice: 2.50,
                variance: 0.1
            },
            {
                label: 'Claude 3.5 Sonnet',
                color: '#d2691e',
                basePrice: 3.00,
                variance: 0.15
            },
            {
                label: 'Gemini 1.5 Pro',
                color: '#4285f4',
                basePrice: 1.25,
                variance: 0.08
            }
        ];
        
        const datasets = models.map(model => {
            const data = dates.map((date, index) => {
                // 가격 변동 시뮬레이션
                let price = model.basePrice;
                if (index > 20) {
                    // 최근 10일간 약간의 가격 변동
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
        
        // 샘플 데이터 안내 메시지
        const container = canvas.parentElement;
        const notice = document.createElement('div');
        notice.className = 'mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg text-sm text-yellow-800 dark:text-yellow-200';
        notice.innerHTML = `
            <div class="flex items-center gap-2">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                </svg>
                <span>현재 샘플 데이터를 표시하고 있습니다. 실제 데이터는 GitHub Actions를 통해 수집됩니다.</span>
            </div>
        `;
        container.appendChild(notice);
    }
    
    destroy() {
        // 모든 차트 정리
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}