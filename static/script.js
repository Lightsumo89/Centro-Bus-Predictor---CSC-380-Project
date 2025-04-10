document.addEventListener('DOMContentLoaded', function() {    
  const menuBtn = document.getElementById('menuBtn');
  const menuContainer = document.getElementById('menuContainer');
  
  if (menuBtn && menuContainer) {
    menuBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      menuContainer.classList.toggle('active');
    });

    document.addEventListener('click', function(e) {
      if (!menuContainer.contains(e.target) && menuContainer.classList.contains('active')) {
        menuContainer.classList.remove('active');
      }
    });
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && menuContainer.classList.contains('active')) {
        menuContainer.classList.remove('active');
      }
    });
  }
  

  const carouselItems = document.querySelectorAll('.carousel-item');
  let currentIndex = 0;
  const intervalTime = 10000; 
  
  function nextSlide() {
      let nextIndex;
      do {
          nextIndex = Math.floor(Math.random() * carouselItems.length);
      } while (nextIndex === currentIndex && carouselItems.length > 1);
      
    
      carouselItems[currentIndex].classList.remove('active');
      carouselItems[nextIndex].classList.add('active');
      currentIndex = nextIndex;
  }
  

  if (carouselItems.length > 0) {
      carouselItems[0].classList.add('active');
      let carouselInterval = setInterval(nextSlide, intervalTime);
      const hero = document.querySelector('.hero');
      if (hero) {
          hero.addEventListener('mouseenter', () => {
              clearInterval(carouselInterval);
          });
          
          hero.addEventListener('mouseleave', () => {
              carouselInterval = setInterval(nextSlide, intervalTime);
          });
      }
  }

  const backToTopButton = document.createElement('a');
  backToTopButton.href = '#';
  backToTopButton.className = 'back-to-top';
  backToTopButton.innerHTML = '&#8593;';
  backToTopButton.setAttribute('aria-label', 'Back to top');
  document.body.appendChild(backToTopButton);
  
  window.addEventListener('scroll', function() {
      if (window.pageYOffset > 300) {
          backToTopButton.classList.add('visible');
      } else {
          backToTopButton.classList.remove('visible');
      }
  });
  
  backToTopButton.addEventListener('click', function(e) {
      e.preventDefault();
      window.scrollTo({
          top: 0,
          behavior: 'smooth'
      });
  });
  const currentPage = window.location.pathname.split('/').pop();
  const menuLinks = document.querySelectorAll('.dropdown-menu a');
  
  menuLinks.forEach(link => {
      const linkPage = link.getAttribute('href');
      if (linkPage === currentPage) {
          link.classList.add('active');
          const parentItem = link.closest('.dropdown-item');
          if (parentItem && parentItem.querySelector('button')) {
              parentItem.querySelector('button').classList.add('active');
          }
      }
  });
});