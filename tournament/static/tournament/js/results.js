// Dynamic results loading via Fetch API — no page reload needed
document.addEventListener('DOMContentLoaded', function () {
  const refreshBtn = document.getElementById('refreshResults');
  const container = document.getElementById('resultsContainer');

  if (!refreshBtn || !container) return;

  refreshBtn.addEventListener('click', loadResults);

  function loadResults() {
    refreshBtn.disabled = true;
    refreshBtn.textContent = 'Loading...';

    fetch('/api/results/')
      .then(function (res) { return res.json(); })
      .then(function (data) { renderResults(data.results); })
      .catch(function () {
        container.innerHTML = '<p class="empty-state">Failed to load results. Please try again.</p>';
      })
      .finally(function () {
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = '&#8635; Refresh';
      });
  }

  function renderResults(results) {
    if (!results || results.length === 0) {
      container.innerHTML = '<p class="empty-state">No completed matches yet.</p>';
      return;
    }

    container.innerHTML =
      '<div class="result-grid">' +
      results.map(function (r) {
        var t1Win = r.winner === r.team1;
        var t2Win = r.winner === r.team2;
        return (
          '<div class="result-card glass" data-match-id="' + r.id + '">' +
            '<div class="result-teams">' +
              '<div class="result-team ' + (t1Win ? 'winner' : '') + '">' +
                '<img src="' + r.team1_logo + '" alt="' + r.team1 + '" class="team-logo-sm">' +
                '<div><p class="result-team-name">' + r.team1 + '</p>' +
                '<p class="result-score">' + r.team1_score + '</p></div>' +
                (t1Win ? '<span class="winner-tag">&#127942;</span>' : '') +
              '</div>' +
              '<span class="vs">VS</span>' +
              '<div class="result-team ' + (t2Win ? 'winner' : '') + '">' +
                '<img src="' + r.team2_logo + '" alt="' + r.team2 + '" class="team-logo-sm">' +
                '<div><p class="result-team-name">' + r.team2 + '</p>' +
                '<p class="result-score">' + r.team2_score + '</p></div>' +
                (t2Win ? '<span class="winner-tag">&#127942;</span>' : '') +
              '</div>' +
            '</div>' +
            '<div class="result-footer">' +
              '<p>&#128205; ' + r.venue + '</p>' +
              '<p>&#128197; ' + r.date + '</p>' +
            '</div>' +
            '<p class="result-winner-text">' +
              (r.winner ? r.winner + ' won the match' : 'No result') +
            '</p>' +
          '</div>'
        );
      }).join('') +
      '</div>';
  }
});
