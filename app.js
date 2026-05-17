document.addEventListener("DOMContentLoaded", () => {
    const btnListado = document.getElementById("btn-listado");
    const btnGestion = document.getElementById("btn-gestion");
    const vistaListado = document.getElementById("vista-listado");
    const vistaGestion = document.getElementById("vista-gestion");

    if (btnListado && btnGestion) {
        btnListado.addEventListener("click", () => {
            btnListado.classList.add("active");
            btnGestion.classList.remove("active");
            vistaListado.classList.add("active");
            vistaGestion.classList.remove("active");
        });

        btnGestion.addEventListener("click", () => {
            btnGestion.classList.add("active");
            btnListado.classList.remove("active");
            vistaGestion.classList.add("active");
            vistaListado.classList.remove("active");
        });
    }
});