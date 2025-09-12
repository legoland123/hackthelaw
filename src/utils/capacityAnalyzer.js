/**
 * Capacity Analyzer - Helps users understand system limits and optimize content
 */

import documentProcessor from '../services/documentProcessor';

class CapacityAnalyzer {
    constructor() {
        this.limits = documentProcessor.getRecommendedLimits();
    }

    /**
     * Analyze project capacity and provide recommendations
     * @param {Array} documents - Array of project documents
     * @returns {Object} Capacity analysis and recommendations
     */
    analyzeProjectCapacity(documents) {
        const validDocuments = documents.filter(doc => {
            const content = doc.content || '';
            return documentProcessor.isValidContent(content);
        });

        const totalChars = validDocuments.reduce((sum, doc) => {
            return sum + (doc.content?.length || 0);
        }, 0);

        const totalWords = documentProcessor.estimateWordCount(totalChars);
        const estimatedTokens = documentProcessor.estimateTokenCount(totalWords);

        // Calculate capacity usage for each scenario
        const capacityUsage = {};
        Object.keys(this.limits).forEach(scenario => {
            const limit = this.limits[scenario];
            const charUsage = (totalChars / (limit.maxCharsPerDoc * limit.maxDocsPerProject)) * 100;
            const wordUsage = (totalWords / limit.maxTotalWords) * 100;

            capacityUsage[scenario] = {
                charUsage: Math.min(charUsage, 100),
                wordUsage: Math.min(wordUsage, 100),
                isWithinLimits: charUsage <= 100 && wordUsage <= 100,
                recommendation: this.getRecommendation(scenario, charUsage, wordUsage)
            };
        });

        return {
            summary: {
                totalDocuments: documents.length,
                validDocuments: validDocuments.length,
                totalCharacters: totalChars,
                totalWords: totalWords,
                estimatedTokens: estimatedTokens,
                averageWordsPerDoc: validDocuments.length > 0 ? Math.round(totalWords / validDocuments.length) : 0
            },
            capacityUsage,
            recommendations: this.getOverallRecommendations(totalWords, validDocuments.length),
            limits: this.limits
        };
    }

    /**
     * Get recommendation for a specific scenario
     * @param {string} scenario - Scenario name
     * @param {number} charUsage - Character usage percentage
     * @param {number} wordUsage - Word usage percentage
     * @returns {string} Recommendation message
     */
    getRecommendation(scenario, charUsage, wordUsage) {
        if (charUsage <= 100 && wordUsage <= 100) {
            return `✅ Within ${scenario} limits - ${this.limits[scenario].description}`;
        } else {
            const issues = [];
            if (charUsage > 100) issues.push('character limit');
            if (wordUsage > 100) issues.push('word limit');
            return `⚠️ Exceeds ${scenario} ${issues.join(' and ')}`;
        }
    }

    /**
     * Get overall recommendations for the project
     * @param {number} totalWords - Total word count
     * @param {number} docCount - Number of documents
     * @returns {Array} Array of recommendation messages
     */
    getOverallRecommendations(totalWords, docCount) {
        const recommendations = [];

        // Check if within conservative limits
        if (totalWords <= this.limits.conservative.maxTotalWords && docCount <= this.limits.conservative.maxDocsPerProject) {
            recommendations.push({
                type: 'success',
                message: '✅ Your project is well within recommended limits for optimal performance.',
                details: 'You can expect fast, reliable responses from the AI assistant.'
            });
        }

        // Check if approaching moderate limits
        if (totalWords > this.limits.conservative.maxTotalWords && totalWords <= this.limits.moderate.maxTotalWords) {
            recommendations.push({
                type: 'warning',
                message: '⚠️ Your project is approaching moderate capacity limits.',
                details: 'Consider optimizing document content or splitting large documents for better performance.'
            });
        }

        // Check if exceeding moderate limits
        if (totalWords > this.limits.moderate.maxTotalWords) {
            recommendations.push({
                type: 'error',
                message: '❌ Your project exceeds recommended capacity limits.',
                details: 'Consider reducing document content or using document summaries to improve AI performance.'
            });
        }

        // Document count recommendations
        if (docCount > this.limits.moderate.maxDocsPerProject) {
            recommendations.push({
                type: 'warning',
                message: '📄 High document count detected.',
                details: 'Consider consolidating similar documents or using document summaries to reduce context load.'
            });
        }

        return recommendations;
    }

    /**
     * Get capacity display information for UI
     * @param {Object} analysis - Capacity analysis result
     * @returns {Object} Formatted display information
     */
    getDisplayInfo(analysis) {
        const bestScenario = Object.keys(analysis.capacityUsage).find(scenario =>
            analysis.capacityUsage[scenario].isWithinLimits
        ) || 'unlimited';

        return {
            currentUsage: {
                documents: analysis.summary.validDocuments,
                words: analysis.summary.totalWords,
                tokens: analysis.summary.estimatedTokens,
                averageWordsPerDoc: analysis.summary.averageWordsPerDoc
            },
            bestScenario: {
                name: bestScenario,
                limit: this.limits[bestScenario],
                usage: analysis.capacityUsage[bestScenario]
            },
            recommendations: analysis.recommendations,
            allScenarios: Object.keys(this.limits).map(scenario => ({
                name: scenario,
                limit: this.limits[scenario],
                usage: analysis.capacityUsage[scenario]
            }))
        };
    }

    /**
     * Format capacity information for display
     * @param {number} number - Number to format
     * @param {string} type - Type of number (words, chars, tokens)
     * @returns {string} Formatted string
     */
    formatNumber(number, type = 'words') {
        if (number >= 1000000) {
            return `${(number / 1000000).toFixed(1)}M ${type}`;
        } else if (number >= 1000) {
            return `${(number / 1000).toFixed(1)}K ${type}`;
        } else {
            return `${number.toLocaleString()} ${type}`;
        }
    }
}

// Export singleton instance
export const capacityAnalyzer = new CapacityAnalyzer();
export default capacityAnalyzer; 