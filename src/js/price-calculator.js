export class PriceCalculator {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.selectedModels = new Set();
        this.usageScenario = {
            inputTokens: 1000000,  // 1M tokens
            outputTokens: 500000,  // 500K tokens
            requestsPerMonth: 1000
        };
        this.debounceTimer = null;
        this.debounceDelay = 500; // 500ms debounce

        this.init();
    }

    init() {
        this.renderCalculator();
        this.setupEventListeners();
    }

    // Debounce function for auto-calculation
    debounce(func, delay) {
        return (...args) => {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => func.apply(this, args), delay);
        };
    }

    // Validate input value
    validateInput(value, min = 0, max = 1000000000) {
        const numValue = parseInt(value) || 0;
        return Math.max(min, Math.min(max, numValue));
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
                        <fieldset>
                            <legend class="font-semibold text-gray-900 dark:text-white mb-4">월간 예상 사용량</legend>

                            <div class="space-y-3">
                                <div>
                                    <label for="inputTokens" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        입력 토큰 수
                                    </label>
                                    <input
                                        type="number"
                                        id="inputTokens"
                                        name="inputTokens"
                                        value="${this.usageScenario.inputTokens}"
                                        min="0"
                                        max="1000000000"
                                        step="1000"
                                        aria-label="입력 토큰 수"
                                        aria-describedby="inputTokens-help"
                                        class="calculator-number-input w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                        required
                                    >
                                    <small id="inputTokens-help" class="text-gray-500 dark:text-gray-400">1M tokens ≈ 750,000 단어</small>
                                    <div id="inputTokens-error" class="text-red-500 text-sm mt-1 hidden" role="alert"></div>
                                </div>

                                <div>
                                    <label for="outputTokens" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        출력 토큰 수
                                    </label>
                                    <input
                                        type="number"
                                        id="outputTokens"
                                        name="outputTokens"
                                        value="${this.usageScenario.outputTokens}"
                                        min="0"
                                        max="1000000000"
                                        step="1000"
                                        aria-label="출력 토큰 수"
                                        aria-describedby="outputTokens-help"
                                        class="calculator-number-input w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                        required
                                    >
                                    <small id="outputTokens-help" class="text-gray-500 dark:text-gray-400">모델이 생성하는 토큰 수</small>
                                    <div id="outputTokens-error" class="text-red-500 text-sm mt-1 hidden" role="alert"></div>
                                </div>

                                <div>
                                    <label for="requestsPerMonth" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        월간 요청 수
                                    </label>
                                    <input
                                        type="number"
                                        id="requestsPerMonth"
                                        name="requestsPerMonth"
                                        value="${this.usageScenario.requestsPerMonth}"
                                        min="1"
                                        max="100000000"
                                        step="100"
                                        aria-label="월간 요청 수"
                                        aria-describedby="requestsPerMonth-help"
                                        class="calculator-number-input w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                        required
                                    >
                                    <small id="requestsPerMonth-help" class="text-gray-500 dark:text-gray-400">API 호출 횟수</small>
                                    <div id="requestsPerMonth-error" class="text-red-500 text-sm mt-1 hidden" role="alert"></div>
                                </div>
                            </div>
                        </fieldset>

                        <!-- 빠른 시나리오 선택 -->
                        <fieldset class="pt-4">
                            <legend class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">빠른 시나리오 선택</legend>
                            <div class="grid grid-cols-2 gap-2">
                                <button type="button" class="scenario-btn px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                                        data-scenario="small"
                                        aria-label="소규모 시나리오 선택: 10만 토큰/월">
                                    소규모 (10만 토큰/월)
                                </button>
                                <button type="button" class="scenario-btn px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                                        data-scenario="medium"
                                        aria-label="중규모 시나리오 선택: 100만 토큰/월">
                                    중규모 (100만 토큰/월)
                                </button>
                                <button type="button" class="scenario-btn px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                                        data-scenario="large"
                                        aria-label="대규모 시나리오 선택: 1000만 토큰/월">
                                    대규모 (1000만 토큰/월)
                                </button>
                                <button type="button" class="scenario-btn px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                                        data-scenario="enterprise"
                                        aria-label="엔터프라이즈 시나리오 선택: 1억 토큰/월">
                                    엔터프라이즈 (1억 토큰/월)
                                </button>
                            </div>
                        </fieldset>
                    </div>

                    <!-- 모델 선택 -->
                    <div class="space-y-4">
                        <fieldset>
                            <div class="flex items-center justify-between mb-4">
                                <legend class="font-semibold text-gray-900 dark:text-white">비교할 모델 선택</legend>
                                <span id="modelSelectionCounter" class="text-sm text-gray-500 dark:text-gray-400" aria-live="polite">
                                    선택됨: <span class="font-semibold text-blue-600 dark:text-blue-400">0</span>개
                                </span>
                            </div>

                            <!-- 선택 컨트롤 버튼 -->
                            <div class="flex gap-2 mb-3">
                                <button type="button" id="selectAllModels" class="flex-1 px-3 py-1.5 text-sm bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors" aria-label="모든 모델 선택">
                                    전체 선택
                                </button>
                                <button type="button" id="deselectAllModels" class="flex-1 px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors" aria-label="모든 모델 선택 해제">
                                    전체 해제
                                </button>
                            </div>

                            <div id="modelCheckboxes" class="space-y-2 max-h-96 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg p-3" role="group" aria-label="모델 선택 목록">
                                <!-- 모델 체크박스가 여기에 삽입됨 -->
                            </div>
                        </fieldset>

                        <button type="button" id="calculateCosts" class="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed" aria-label="선택한 모델의 비용 계산하기">
                            비용 계산하기
                        </button>
                    </div>
                </div>

                <!-- 계산 결과 -->
                <div id="calculatorResults" class="mt-8" role="region" aria-live="polite" aria-label="계산 결과">
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
            <div class="mb-4 last:mb-0">
                <div class="flex items-center justify-between mb-2 pb-2 border-b border-gray-200 dark:border-gray-600">
                    <h5 class="text-sm font-medium text-gray-700 dark:text-gray-300">
                        ${this.dashboard.data.providers[provider]?.name || provider}
                    </h5>
                    <button
                        type="button"
                        class="provider-toggle text-xs px-2 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
                        data-provider="${provider}"
                        aria-label="${this.dashboard.data.providers[provider]?.name || provider} 모델 전체 선택/해제"
                    >
                        전체 선택
                    </button>
                </div>
                ${models.map(model => `
                    <label class="flex items-center p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded cursor-pointer transition-colors">
                        <input
                            type="checkbox"
                            value="${model.id}"
                            class="model-checkbox w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 mr-3"
                            data-provider="${provider}"
                            ${this.selectedModels.has(model.id) ? 'checked' : ''}
                            aria-label="${model.name} 선택"
                        >
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2">
                                <span class="font-medium text-gray-900 dark:text-white truncate">${model.name}</span>
                                <span class="text-sm text-gray-500 dark:text-gray-400 calculator-number-display whitespace-nowrap">
                                    $${(model.pricing?.input || model.input_price || 0).toFixed(2)}/1M
                                </span>
                            </div>
                        </div>
                    </label>
                `).join('')}
            </div>
        `).join('');

        this.updateSelectionCounter();
    }

    // Update the selection counter
    updateSelectionCounter() {
        const counter = document.querySelector('#modelSelectionCounter span');
        if (counter) {
            counter.textContent = this.selectedModels.size;
        }
    }
    
    setupEventListeners() {
        // Create debounced auto-calculate function
        const debouncedCalculate = this.debounce(() => {
            if (this.selectedModels.size > 0) {
                this.calculateAndDisplay();
            }
        }, this.debounceDelay);

        // 사용량 입력 변경 with validation and auto-calculate
        ['inputTokens', 'outputTokens', 'requestsPerMonth'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('input', (e) => {
                    const input = e.target;
                    const min = parseInt(input.getAttribute('min')) || 0;
                    const max = parseInt(input.getAttribute('max')) || 1000000000;
                    const value = input.value;

                    // Validate input
                    const errorElement = document.getElementById(`${id}-error`);
                    if (value === '' || value < 0) {
                        errorElement.textContent = '0 이상의 값을 입력해주세요.';
                        errorElement.classList.remove('hidden');
                        input.classList.add('border-red-500');
                        return;
                    } else if (parseInt(value) > max) {
                        errorElement.textContent = `${max.toLocaleString()} 이하의 값을 입력해주세요.`;
                        errorElement.classList.remove('hidden');
                        input.classList.add('border-red-500');
                        return;
                    } else {
                        errorElement.classList.add('hidden');
                        input.classList.remove('border-red-500');
                    }

                    // Update scenario
                    const validatedValue = this.validateInput(value, min, max);
                    this.usageScenario[id] = validatedValue;

                    // Auto-calculate with debounce
                    debouncedCalculate();
                });

                // Prevent negative numbers on blur
                element.addEventListener('blur', (e) => {
                    const input = e.target;
                    if (input.value === '' || parseInt(input.value) < 0) {
                        input.value = 0;
                        this.usageScenario[input.id] = 0;
                    }
                });
            }
        });

        // 시나리오 버튼
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('scenario-btn')) {
                this.applyScenario(e.target.getAttribute('data-scenario'));
            }
        });

        // Select All Models button
        const selectAllBtn = document.getElementById('selectAllModels');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                this.selectAllModels();
            });
        }

        // Deselect All Models button
        const deselectAllBtn = document.getElementById('deselectAllModels');
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => {
                this.deselectAllModels();
            });
        }

        // Provider-level toggles
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('provider-toggle')) {
                const provider = e.target.getAttribute('data-provider');
                this.toggleProvider(provider);
            }
        });

        // 모델 선택 with auto-calculate
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('model-checkbox')) {
                if (e.target.checked) {
                    this.selectedModels.add(e.target.value);
                } else {
                    this.selectedModels.delete(e.target.value);
                }
                this.updateSelectionCounter();

                // Auto-calculate with debounce
                debouncedCalculate();
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

    // Select all models
    selectAllModels() {
        const checkboxes = document.querySelectorAll('.model-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            this.selectedModels.add(checkbox.value);
        });
        this.updateSelectionCounter();

        // Auto-calculate after selection
        if (this.selectedModels.size > 0) {
            this.calculateAndDisplay();
        }
    }

    // Deselect all models
    deselectAllModels() {
        const checkboxes = document.querySelectorAll('.model-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        this.selectedModels.clear();
        this.updateSelectionCounter();

        // Clear results
        const resultsContainer = document.getElementById('calculatorResults');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
        }
    }

    // Toggle all models for a specific provider
    toggleProvider(provider) {
        const checkboxes = document.querySelectorAll(`.model-checkbox[data-provider="${provider}"]`);
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);

        checkboxes.forEach(checkbox => {
            checkbox.checked = !allChecked;
            if (!allChecked) {
                this.selectedModels.add(checkbox.value);
            } else {
                this.selectedModels.delete(checkbox.value);
            }
        });

        this.updateSelectionCounter();

        // Auto-calculate after toggle
        if (this.selectedModels.size > 0) {
            this.calculateAndDisplay();
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

        const maxCost = Math.max(...results.map(r => r.totalCost));

        container.innerHTML = `
            <div class="border-t dark:border-gray-700 pt-6">
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">📊 월간 예상 비용</h4>

                <!-- Visual Cost Comparison Chart -->
                <div class="mb-8">
                    <h5 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">비용 비교 차트</h5>
                    <div class="space-y-3">
                        ${results.map((result, index) => {
                            const percentage = (result.totalCost / maxCost) * 100;
                            const isLowest = index === 0;
                            return `
                                <div class="relative">
                                    <div class="flex items-center justify-between mb-1">
                                        <div class="flex items-center gap-2">
                                            <span class="text-sm font-medium text-gray-900 dark:text-white">${result.model.name}</span>
                                            ${isLowest ? '<span class="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded">최저가</span>' : ''}
                                        </div>
                                        <span class="text-sm font-semibold calculator-number-display text-gray-900 dark:text-white">$${result.totalCost.toFixed(2)}</span>
                                    </div>
                                    <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-8 overflow-hidden">
                                        <div
                                            class="h-full flex items-center px-3 text-xs font-medium text-white transition-all duration-500 ${isLowest ? 'bg-green-500' : 'bg-blue-500'}"
                                            style="width: ${percentage}%"
                                            role="progressbar"
                                            aria-valuenow="${percentage.toFixed(0)}"
                                            aria-valuemin="0"
                                            aria-valuemax="100"
                                            aria-label="${result.model.name} 비용 비율"
                                        >
                                            <span class="calculator-number-display">${percentage.toFixed(1)}%</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>

                <!-- Cost Table -->
                <div class="overflow-x-auto">
                    <div class="mb-4">
                        <h5 class="text-sm font-medium text-gray-700 dark:text-gray-300">상세 비용 분석</h5>
                    </div>
                    <div class="calculator-table-wrapper">
                        <table class="w-full calculator-table">
                            <thead>
                                <tr class="border-b-2 border-gray-300 dark:border-gray-600">
                                    <th class="text-left py-3 px-4 font-semibold text-gray-900 dark:text-white">모델</th>
                                    <th class="text-right py-3 px-4 font-semibold text-gray-900 dark:text-white">입력 비용</th>
                                    <th class="text-right py-3 px-4 font-semibold text-gray-900 dark:text-white">출력 비용</th>
                                    <th class="text-right py-3 px-4 font-semibold text-gray-900 dark:text-white">총 비용</th>
                                    <th class="text-right py-3 px-4 font-semibold text-gray-900 dark:text-white">요청당 비용</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${results.map((result, index) => `
                                    <tr class="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors ${index === 0 ? 'bg-green-50 dark:bg-green-900/20' : ''}">
                                        <td class="py-3 px-4">
                                            <div>
                                                <div class="font-medium text-gray-900 dark:text-white">${result.model.name}</div>
                                                <div class="text-sm text-gray-500 dark:text-gray-400">
                                                    ${this.dashboard.data.providers[result.model.provider]?.name || result.model.provider}
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-3 px-4 text-right calculator-number-display">$${result.inputCost.toFixed(2)}</td>
                                        <td class="py-3 px-4 text-right calculator-number-display">$${result.outputCost.toFixed(2)}</td>
                                        <td class="py-3 px-4 text-right font-semibold calculator-number-display text-gray-900 dark:text-white">$${result.totalCost.toFixed(2)}</td>
                                        <td class="py-3 px-4 text-right text-sm text-gray-500 dark:text-gray-400 calculator-number-display">
                                            $${result.costPerRequest.toFixed(4)}
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>

                ${results.length > 1 ? this.generateSavingsAnalysis(results) : ''}

                <!-- 연간 예상 비용 -->
                <div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <h5 class="font-semibold text-blue-900 dark:text-blue-300 mb-3">연간 예상 비용</h5>
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                        ${results.slice(0, 4).map(result => `
                            <div class="bg-white dark:bg-gray-800 rounded-lg p-3">
                                <div class="text-sm text-gray-600 dark:text-gray-400 truncate">${result.model.name}</div>
                                <div class="font-semibold text-lg calculator-number-display text-gray-900 dark:text-white mt-1">
                                    $${(result.totalCost * 12).toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0})}
                                </div>
                                <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    월 $${result.totalCost.toFixed(2)}
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