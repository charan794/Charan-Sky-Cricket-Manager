// Dynamic points table loading via Fetch API — no page reload needed
document.addEventListener('DOMContentLoaded', function () {
  const refreshBtn = document.getElementById('refreshPoints');
  const tbody = document.getElementById('pointsBody');

  if (!refreshBtn || !tbody) return;

  refreshBtn.addEventListener('click', loadPoints);

  function loadPoints() {
    refreshBtn.disabled = true;
    refreshBtn.textContent = 'Loading...';

    fetch('/api/points-table/')
      .then(function (res) { return res.json(); })
      .then(function (data) { renderPoints(data.points_table); })
      .catch(function () {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Failed to load standings.</td></tr>';
      })
      .finally(function () {
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = '&#8635; Refresh';
      });
  }

  function renderPoints(table) {
    if (!table || table.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No standings available.</td></tr>';
      return;
    }

    tbody.innerHTML = table.map(function (pt, i) {
      var leaderClass = i === 0 && pt.played > 0 ? 'leader-row' : '';
      return (
        '<tr class="' + leaderClass + '">' +
          '<td class="rank-cell">' + (i + 1) + '</td>' +
          '<td class="team-cell">' +
            '<img src="' + pt.logo + '" alt="' + pt.team + '" class="team-logo-xs">' +
            pt.team +
          '</td>' +
          '<td>' + pt.played + '</td>' +
          '<td class="win-cell">' + pt.wins + '</td>' +
          '<td class="loss-cell">' + pt.losses + '</td>' +
          '<td class="points-cell">' + pt.points + '</td>' +
        '</tr>'
      );
    }).join('');
  }
});
