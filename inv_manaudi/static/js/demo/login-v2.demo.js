/*
 * Selector de fondo de la pantalla de login (reemplaza el demo del tema Color Admin).
 */
(function () {
	function cambiarFondo(elm) {
		var img = elm.getAttribute('data-img');
		var cover = document.querySelector('.login-cover-img');
		if (cover && img) {
			cover.style.backgroundImage = 'url(' + img + ')';
		}
		var activos = document.querySelectorAll('.login-bg-list-item.active');
		for (var i = 0; i < activos.length; i++) {
			activos[i].classList.remove('active');
		}
		if (elm.parentNode) {
			elm.parentNode.classList.add('active');
		}
	}
	document.addEventListener('DOMContentLoaded', function () {
		var enlaces = document.querySelectorAll('[data-toggle="login-change-bg"]');
		for (var i = 0; i < enlaces.length; i++) {
			enlaces[i].addEventListener('click', function (e) {
				e.preventDefault();
				cambiarFondo(this);
			});
		}
	});
})();
