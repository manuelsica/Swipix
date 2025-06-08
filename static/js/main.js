document.addEventListener('DOMContentLoaded', () => {
  initializeSwipe();
  const btn = document.getElementById('generateBtn');
  if (btn) btn.addEventListener('click', generateRecommendations);
});

function generateRecommendations() {
  const stack  = document.getElementById('cardStack');
  const empty  = document.getElementById('emptyState');
  const loader = document.getElementById('loadingOverlay');

  loader.style.display = 'flex';

  fetch('/recommend', { method: 'POST' })
    .then(r => r.json())
    .then(movies => {
      // ricrea 5 card
      stack.innerHTML = '';
      empty.style.display = 'none';

      movies.forEach(m => {
        stack.insertAdjacentHTML('beforeend', `
          <div class="movie-card" data-movie-id="${m.id}">
            <div class="movie-poster">
              <img src="${m.poster_url}" alt="${m.title}" loading="lazy">
              <div class="movie-rating"><i class="fas fa-star"></i><span>${m.rating}</span></div>
            </div>
            <div class="movie-info">
              <h3 class="movie-title">${m.title}</h3>
              <div class="movie-meta">
                <span class="genre">${m.genre.replace(/\|/g, ', ')}</span>
                <span class="year">${m.year}</span>
              </div>
              <div class="movie-director"><i class="fas fa-user-tie me-1"></i>Diretto da ${m.director}</div>
            </div>
            <div class="card-actions">
              <button class="btn btn-dislike" onclick="rateMovie(${m.id}, false)"><i class="fas fa-times"></i></button>
              <button class="btn btn-like"    onclick="rateMovie(${m.id}, true)"><i class="fas fa-heart"></i></button>
            </div>
            <div class="swipe-indicator like-indicator"><i class="fas fa-heart"></i><span>MI PIACE</span></div>
            <div class="swipe-indicator dislike-indicator"><i class="fas fa-times"></i><span>PASSA</span></div>
          </div>`);
      });

      initializeSwipe();           // ri-aggancia lo swipe
    })
    .finally(() => { loader.style.display = 'none'; });
}
