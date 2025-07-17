export class PriceCalculator {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.selectedModels = new Set();
        this.usageScenario = {
            inputTokens: 1000000,  // 1M tokens
            outputTokens: 500000,  // 500K tokens
            requestsPerMonth: 1000
        };
        
        this.init();
    }
    
    init() {
        this.renderCalculator();
        this.setupEventListeners();
    }
    
    renderCalculator() {
        const calculatorContainer = document.getElementById('priceCalculator');
        if (!calculatorContainer) return;
        
        calculatorContainer.innerHTML = `
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-6">💰 비용 계산기</h3>
                
                <div class="grid md:grid-cols-2 gap-6">
                    <!-- 사용량 입력 -->
                    <div class="space-y-4">
                        <h4 class="font-semibold text-gray-900 dark:text-white">월간 예상 사용량</h4>
                        
                        <div class="space-y-3">
                            <div>
                                <label for="inputTokens" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    입력 토큰 수
                                </label>
                                <input 
                                    type="number" 
                                    id="inputTokens" 
                                    value="${this.usageScenario.inputTokens}" 
                                    min="0"
                                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                >
                                <small class="text-gray-500 dark:text-gray-400">1M tokens ≈ 750,000 단어</small>
                            </div>
                            
                            <div>
                                <label for="outputTokens" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    출력 토큰 수
                                </label>
                                <input 
                                    type="number" 
                                    id="outputTokens" 
                                    value="${this.usageScenario.outputTokens}" 
                                    min="0"
                                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                >
                            </div>
                            
                            <div>
                                <label for="requestsPerMonth" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    월간 요청 수
                                </label>
                                <input 
                                    type="number" 
                                    id="requestsPerMonth" 
                                    value="${this.usageScenario.requestsPerMonth}" 
                                    min="0"
                                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                >
                            </div>
                        </div>
                        
                        <!-- 빠른 시나리오 선택 -->
                        <div class="pt-4">
                            <h5 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">빠른 시나리오 선택</h5>
                            <div class="grid grid-cols-2 gap-2">
                                <button class="scenario-btn px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600" 
                                        data-scenario="small">
                                    소규모 (10만 토큰/월)
                                </button>
                                <button class="scenario-btn px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600" 
                                        data-scenario="medium">
                                    중규모 (100만 토큰/월)
                                </button>
                                <button class="scenario-btn px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600" 
                                        data-scenario="large">
                                    대규모 (1000만 토큰/월)
                                </button>
                                <button class="scenario-btn px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600" 
                                        data-scenario="enterprise">
                                    엔터프라이즈 (1억 토큰/월)
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 모델 선택 -->
                    <div class="space-y-4">
                        <h4 class="font-semibold text-gray-900 dark:text-white">비교할 모델 선택</h4>
                        
                        <div id="modelCheckboxes" class="space-y-2 max-h-96 overflow-y-auto">
                            <!-- 모델 체크박스가 여기에 삽입됨 -->
                        </div>
                        
                        <button id="calculateCosts" class="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium">
                            비용 계산하기
                        </button>
                    </div>
                </div>
                
                <!-- 계산 결과 -->
                <div id="calculatorResults" class="mt-8">
                    <!-- 결과가 여기에 표시됨 -->
                </div>
            </div>
        `;
        
        this.renderModelCheckboxes();
    }
    
    renderModelCheckboxes() {
        const container = document.getElementById('modelCheckboxes');
        if (!container) return;
        
        // 가격이 있는 모델만 필터링하고 가격순으로 정렬
        const models = this.dashboard.data.models
            .filter(model => {
                const inputPrice = model.pricing?.input || model.input_price || 0;
                return inputPrice > 0;
            })
            .sort((a, b) => {
                const priceA = a.pricing?.input || a.input_price || 0;
                const priceB = b.pricing?.input || b.input_price || 0;
                return priceA - priceB;
            });
        
        // 제공업체별로 그룹화
        const groupedModels = {};
        models.forEach(model => {
            const provider = model.provider;
            if (!groupedModels[provider]) {
                groupedModels[provider] = [];
            }
            groupedModels[provider].push(model);
        });
        
        container.innerHTML = Object.entries(groupedModels).map(([provider, models]) => `
            <div class="mb-4">
                <h5 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    ${this.dashboard.data.providers[provider]?.name || provider}
                </h5>
                ${models.map(model => `
                    <label class="flex items-center p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded cursor-pointer">
                        <input 
                            type="checkbox" 
                            value="${model.id}" 
                            class="model-checkbox mr-3"
                            ${this.selectedModels.has(model.id) ? 'checked' : ''}
                        >
                        <div class="flex-1">
                            <span class="font-medium text-gray-900 dark:text-white">${model.name}</span>
                            <span class="text-sm text-gray-500 dark:text-gray-400 ml-2">
                                $${(model.pricing?.input || model.input_price || 0).toFixed(2)}/1M
                            </span>
                        </div>
                    </label>
                `).join('')}
            </div>
        `).join('');
    }
    
    setupEventListeners() {
        // 사용량 입력 변경
        ['inputTokens', 'outputTokens', 'requestsPerMonth'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('input', (e) => {
                    this.usageScenario[id] = parseInt(e.target.value) || 0;
                });
            }
        });
        
        // 시나리오 버튼
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('scenario-btn')) {
                this.applyScenario(e.target.getAttribute('data-scenario'));
            }
        });
        
        // 모델 선택
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('model-checkbox')) {
                if (e.target.checked) {
                    this.selectedModels.add(e.target.value);
                } else {
                    this.selectedModels.delete(e.target.value);
                }
            }
        });
        
        // 계산 버튼
        const calculateBtn = document.getElementById('calculateCosts');
        if (calculateBtn) {
            calculateBtn.addEventListener('click', () => {
                this.calculateAndDisplay();
            });
        }
    }
    
    applyScenario(scenario) {
        const scenarios = {
            small: {
                inputTokens: 100000,
                outputTokens: 50000,
                requestsPerMonth: 100
            },
            medium: {
                inputTokens: 1000000,
                outputTokens: 500000,
                requestsPerMonth: 1000
            },
            large: {
                inputTokens: 10000000,
                outputTokens: 5000000,
                requestsPerMonth: 10000
            },
            enterprise: {
                inputTokens: 100000000,
                outputTokens: 50000000,
                requestsPerMonth: 100000
            }
        };
        
        if (scenarios[scenario]) {
            this.usageScenario = scenarios[scenario];
            
            // UI 업데이트
            document.getElementById('inputTokens').value = this.usageScenario.inputTokens;
            document.getElementById('outputTokens').value = this.usageScenario.outputTokens;
            document.getElementById('requestsPerMonth').value = this.usageScenario.requestsPerMonth;
        }
    }
    
    calculateAndDisplay() {
        if (this.selectedModels.size === 0) {
            this.dashboard.showNotification('비교할 모델을 선택해주세요.', 'warning');
            return;
        }
        
        const results = this.calculateCosts();
        this.displayResults(results);
    }
    
    calculateCosts() {
        const results = [];
        
        for (const modelId of this.selectedModels) {
            const model = this.dashboard.data.models.find(m => m.id === modelId);
            if (!model) continue;
            
            const inputPrice = model.pricing?.input || model.input_price || 0;
            const outputPrice = model.pricing?.output || model.output_price || 0;
            
            const inputCost = (this.usageScenario.inputTokens / 1000000) * inputPrice;
            const outputCost = (this.usageScenario.outputTokens / 1000000) * outputPrice;
            const totalCost = inputCost + outputCost;
            
            results.push({
                model,
                inputCost,
                outputCost,
                totalCost,
                costPerRequest: totalCost / this.usageScenario.requestsPerMonth
            });
        }
        
        return results.sort((a, b) => a.totalCost - b.totalCost);
    }
    
    displayResults(results) {
        const container = document.getElementById('calculatorResults');
        if (!container) return;
        
        container.innerHTML = `
            <div class="border-t dark:border-gray-700 pt-6">
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">📊 월간 예상 비용</h4>
                
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead>
                            <tr class="border-b dark:border-gray-700">
                                <th class="text-left py-3 px-4">모델</th>
                                <th class="text-right py-3 px-4">입력 비용</th>
                                <th class="text-right py-3 px-4">출력 비용</th>
                                <th class="text-right py-3 px-4">총 비용</th>
                                <th class="text-right py-3 px-4">요청당 비용</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${results.map((result, index) => `
                                <tr class="border-b dark:border-gray-700 ${index === 0 ? 'bg-green-50 dark:bg-green-900/20' : ''}">
                                    <td class="py-3 px-4">
                                        <div>
                                            <div class="font-medium text-gray-900 dark:text-white">${result.model.name}</div>
                                            <div class="text-sm text-gray-500 dark:text-gray-400">
                                                ${this.dashboard.data.providers[result.model.provider]?.name || result.model.provider}
                                            </div>
                                        </div>
                                    </td>
                                    <td class="py-3 px-4 text-right">$${result.inputCost.toFixed(2)}</td>
                                    <td class="py-3 px-4 text-right">$${result.outputCost.toFixed(2)}</td>
                                    <td class="py-3 px-4 text-right font-semibold">$${result.totalCost.toFixed(2)}</td>
                                    <td class="py-3 px-4 text-right text-sm text-gray-500 dark:text-gray-400">
                                        $${result.costPerRequest.toFixed(4)}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                
                ${results.length > 1 ? this.generateSavingsAnalysis(results) : ''}
                
                <!-- 연간 예상 비용 -->
                <div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <h5 class="font-semibold text-blue-900 dark:text-blue-300 mb-2">연간 예상 비용</h5>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        ${results.slice(0, 4).map(result => `
                            <div>
                                <div class="text-gray-600 dark:text-gray-400">${result.model.name}</div>
                                <div class="font-semibold text-gray-900 dark:text-white">
                                    $${(result.totalCost * 12).toFixed(0).toLocaleString()}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }
    
    generateSavingsAnalysis(results) {
        const cheapest = results[0];
        const mostExpensive = results[results.length - 1];
        const savings = mostExpensive.totalCost - cheapest.totalCost;
        const savingsPercent = ((savings / mostExpensive.totalCost) * 100).toFixed(1);
        
        return `
            <div class="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                <div class="flex items-start gap-3">
                    <span class="text-2xl">💡</span>
                    <div>
                        <p class="font-semibold text-gray-900 dark:text-white">
                            ${cheapest.model.name}를 선택하면 가장 비싼 옵션 대비 
                            <span class="text-green-600 dark:text-green-400">월 $${savings.toFixed(2)} (${savingsPercent}%)</span> 절약
                        </p>
                        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            연간 절약 예상액: <span class="font-semibold">$${(savings * 12).toFixed(0).toLocaleString()}</span>
                        </p>
                    </div>
                </div>
            </div>
        `;
    }
}