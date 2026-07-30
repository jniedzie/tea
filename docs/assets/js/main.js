$(function () {

  function initSearchBox() {
    var pages = new Bloodhound({
      datumTokenizer: Bloodhound.tokenizers.obj.whitespace('title'),
      // datumTokenizer: Bloodhound.tokenizers.whitespace,
      queryTokenizer: Bloodhound.tokenizers.whitespace,

      prefetch: baseurl + '/search.json'
    });

    $('#search-box').typeahead({
      minLength: 0,
      highlight: true
    }, {
        name: 'pages',
        display: 'title',
        source: pages
      });

    $('#search-box').bind('typeahead:select', function (ev, suggestion) {
      window.location.href = suggestion.url;
    });
  }

  function styleContentToMD() {
    $('#markdown-content-container table').addClass('table');
    $('#markdown-content-container img').addClass('img-responsive');
  }

  function initPageToc() {
    var toc = document.querySelector('.page-toc');
    var content = document.getElementById('markdown-content-container');
    if (!toc || !content) return;

    var headings = Array.prototype.slice.call(content.querySelectorAll('h2, h3'));
    if (headings.length < 2) return;

    var list = toc.querySelector('.page-toc-list');
    headings.forEach(function (heading) {
      var item = document.createElement('li');
      var link = document.createElement('a');
      item.className = heading.tagName.toLowerCase() === 'h3' ? 'page-toc-h3' : 'page-toc-h2';
      link.href = '#' + heading.id;
      link.textContent = heading.textContent;
      link.setAttribute('data-toc-id', heading.id);
      item.appendChild(link);
      list.appendChild(item);
    });

    toc.hidden = false;

    var toggle = toc.querySelector('.page-toc-toggle');
    toggle.addEventListener('click', function () {
      var expanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!expanded));
      toc.classList.toggle('is-open', !expanded);
    });

    if ('IntersectionObserver' in window) {
      var links = toc.querySelectorAll('a[data-toc-id]');
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          Array.prototype.forEach.call(links, function (link) {
            link.classList.toggle('active', link.getAttribute('data-toc-id') === entry.target.id);
          });
        });
      }, { rootMargin: '-20% 0px -70% 0px' });
      headings.forEach(function (heading) { observer.observe(heading); });
    }
  }

  function initDocsNav() {
    var nav = document.querySelector('.docs-global-nav');
    if (!nav) return;
    var toggle = nav.querySelector('.docs-nav-toggle');
    toggle.addEventListener('click', function () {
      var expanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!expanded));
      nav.classList.toggle('is-open', !expanded);
    });
  }

  initSearchBox();
  styleContentToMD();
  initDocsNav();
  initPageToc();
});
