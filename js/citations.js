/**
 * citations.js - Real-time Citation Synchronizer and Interactive Counter
 * Connects publications.html with Google Scholar metrics and open academic APIs (OpenAlex).
 */

document.addEventListener('DOMContentLoaded', () => {
    const totalCitationsEl = document.getElementById('total-citations-val');
    const hIndexEl = document.getElementById('h-index-val');
    const i10IndexEl = document.getElementById('i10-index-val');
    const syncStatusEl = document.getElementById('citation-sync-status');

    // Number counting animation helper
    function animateCounter(element, target, duration = 1200) {
        if (!element || isNaN(target)) return;
        const start = parseInt(element.textContent, 10) || 0;
        if (start === target) {
            element.textContent = target;
            return;
        }
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease-out cubic easing
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(start + (target - start) * easeOut);
            element.textContent = current;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.textContent = target;
            }
        }
        requestAnimationFrame(update);
    }

    // Update individual paper badge
    function updatePaperBadge(badgeId, count, url) {
        const badge = document.getElementById(badgeId);
        if (!badge) return;
        const countSpan = badge.querySelector('.citation-num');
        if (countSpan) {
            animateCounter(countSpan, count);
        }
        if (url) {
            badge.setAttribute('href', url);
        }
    }

    // 1. Load baseline citations from data/citations.json
    fetch('./data/citations.json?v=' + Date.now())
        .then(response => {
            if (!response.ok) throw new Error('Citations data not available');
            return response.json();
        })
        .then(data => {
            if (totalCitationsEl && data.total_citations !== undefined) {
                animateCounter(totalCitationsEl, data.total_citations);
            }
            if (hIndexEl && data.h_index !== undefined) {
                animateCounter(hIndexEl, data.h_index);
            }
            if (i10IndexEl && data.i10_index !== undefined) {
                animateCounter(i10IndexEl, data.i10_index);
            }

            // Update paper badges from cached data
            if (data.papers) {
                const p1 = data.papers['10.1016/j.oceaneng.2023.116011'];
                if (p1) {
                    updatePaperBadge('cite-badge-oceaneng', p1.citations, p1.scholar_cites_url);
                }
                const p2 = data.papers['10.1115/OMAE2023-104644'];
                if (p2) {
                    updatePaperBadge('cite-badge-omae', p2.citations, p2.scholar_cites_url);
                }
            }

            if (syncStatusEl && data.last_updated) {
                const dateObj = new Date(data.last_updated);
                syncStatusEl.textContent = `Google Scholar Sync • ${dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}`;
            }

            // 2. Concurrently check live open academic APIs (OpenAlex) for real-time increments
            checkOpenAlexLiveIncrements(data);
        })
        .catch(err => {
            console.warn('Fallback: loaded with pre-rendered citation baseline', err);
        });

    // Check OpenAlex live for any newly indexed citations between scheduled runs
    function checkOpenAlexLiveIncrements(cachedData) {
        const dois = [
            { doi: '10.1016/j.oceaneng.2023.116011', badgeId: 'cite-badge-oceaneng' },
            { doi: '10.1115/OMAE2023-104644', badgeId: 'cite-badge-omae' }
        ];

        let extraCitations = 0;
        let checksCompleted = 0;

        dois.forEach(item => {
            fetch(`https://api.openalex.org/works/https://doi.org/${item.doi}`)
                .then(res => res.json())
                .then(alexWork => {
                    const alexCount = alexWork.cited_by_count || 0;
                    const cachedCount = (cachedData.papers && cachedData.papers[item.doi]) ? cachedData.papers[item.doi].citations : 0;
                    
                    // If OpenAlex detected higher citations than cached
                    if (alexCount > cachedCount) {
                        updatePaperBadge(item.badgeId, alexCount);
                        extraCitations += (alexCount - cachedCount);
                    }
                })
                .catch(() => {})
                .finally(() => {
                    checksCompleted++;
                    if (checksCompleted === dois.length && extraCitations > 0 && totalCitationsEl) {
                        const newTotal = (cachedData.total_citations || 51) + extraCitations;
                        animateCounter(totalCitationsEl, newTotal);
                    }
                });
        });
    }
});
