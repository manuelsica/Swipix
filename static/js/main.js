// main.js

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

  fetch('/recommendations', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ user_id: USER_KEY, top_k: TOP_K })
  })
    .then(r => {
      if (!r.ok) throw new Error(`Server error ${r.status}`);
      return r.json();
    })
    .then(data => {
      const movies = data.recommendations || [];
      stack.innerHTML     = '';
      empty.style.display = 'none';

      movies.forEach(m => {
        // Usa solo i campi disponibili: id, title, rating, genre, year
        stack.insertAdjacentHTML('beforeend', `
          <div class="movie-card" data-movie-id="${m.id}">
            <div class="movie-poster">
              <!-- Se non hai poster_url, metti placeholder o lascia vuoto -->
              <img src="/static/img/placeholder.png" alt="${m.title}" loading="lazy">
              <div class="movie-rating">
                <i class="fas fa-star"></i><span>${m.rating}</span>
              </div>
            </div>
            <div class="movie-info">
              <h3 class="movie-title">${m.title}</h3>
              <div class="movie-meta">
                <span class="genre">${m.genre.replace(/\|/g, ', ')}</span>
                <span class="year">${m.year}</span>
              </div>
            </div>
            <div class="card-actions">
              <button class="btn btn-dislike" onclick="rateMovie(${m.id}, false)">
                <i class="fas fa-times"></i>
              </button>
              <button class="btn btn-like" onclick="rateMovie(${m.id}, true)">
                <i class="fas fa-heart"></i>
              </button>
            </div>
            <div class="swipe-indicator like-indicator">
              <i class="fas fa-heart"></i><span>MI PIACE</span>
            </div>
            <div class="swipe-indicator dislike-indicator">
              <i class="fas fa-times"></i><span>PASSA</span>
            </div>
          </div>
        `);
      });

      initializeSwipe();
    })
    .catch(err => {
      console.error('Errore fetch /recommendations:', err);
      alert('Si è verificato un errore nel caricamento delle raccomandazioni.');
    })
    .finally(() => {
      loader.style.display = 'none';
    });
}
