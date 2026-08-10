<style>
    
    .contenedor-interactivo {
        position: relative;
        display: inline-block;
        max-width: 100%;
    }

    .imagen-fondo {
        display: block;
        width: 100%;
        height: auto;
    }

    
    .punto-interactivo {
        position: absolute;
        width: 24px;
        height: 24px;
        cursor: pointer;
        z-index: 10;
    }

    
    .circulo-pulso {
        width: 100%;
        height: 100%;
        background-color: #ff3b30; 
        border-radius: 50%;
        position: relative;
    }

    
    .circulo-pulso::after {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        border-radius: 50%;
        background-color: rgba(255, 59, 48, 0.6);
        animation: pulso 1.8s infinite ease-out;
    }

    @keyframes pulso {
        0% { transform: scale(1); opacity: 1; }
        100% { transform: scale(3); opacity: 0; }
    }

    
    .cartelito {
        position: absolute;
        bottom: 32px;
        left: 50%;
        transform: translateX(-50%);
        background-color: rgba(0, 0, 0, 0.85);
        color: #fff;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 13px;
        white-space: nowrap;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease, visibility 0.3s ease;
        font-family: sans-serif;
    }

    
    .punto-interactivo:hover .cartelito {
        opacity: 1;
        visibility: visible;
    }

    
    .modal {
        display: none; 
        position: fixed;
        z-index: 100;
        left: 0; top: 0; width: 100%; height: 100%;
        background-color: rgba(0, 0, 0, 0.8);
        justify-content: center;
        align-items: center;
    }

    .contenido-modal {
        position: relative;
        background-color: #000;
        padding: 5px;
        border-radius: 8px;
        width: 90%;
        max-width: 750px;
    }

    
    .cerrar-modal {
        position: absolute;
        top: -40px; right: 0;
        color: #fff;
        font-size: 35px;
        cursor: pointer;
        font-weight: bold;
    }
</style>

<div class="contenedor-interactivo">
    <img src="../imgs_mapa/Mapa_Ibero.png" alt="Mapa interactivo" class="imagen-fondo">

    <div class="punto-interactivo" style="top: 80%; left: 45%;" onclick="abrirModalVideo('../vds_mapa/Oficina_Oliver.mp4')">
        <div class="circulo-pulso"></div>
        <span class="cartelito">Oficina Mecatrónica</span>
    </div>

    <div class="punto-interactivo" style="top: 78%; left: 53%;" onclick="abrirModalVideo('../vds_mapa/Bodega.mp4')">
        <div class="circulo-pulso"></div>
        <span class="cartelito">Almacen</span>
    </div>

    <div class="punto-interactivo" style="top: 29%; left: 31%;" onclick="abrirModalVideo('../vds_mapa/Enfermería.mp4')">
        <div class="circulo-pulso"></div>
        <span class="cartelito">Enfermería</span>
    </div>

    <div class="punto-interactivo" style="top: 20%; left: 60%;" onclick="abrirModalVideo('../vds_mapa/AIDEL.mp4')">
        <div class="circulo-pulso"></div>
        <span class="cartelito">AIDEL</span>
    </div>

    <div class="punto-interactivo" style="top: 27%; left: 52%;" onclick="abrirModalVideo('../vds_mapa/Ciencias_Básicas.mp4')">
        <div class="circulo-pulso"></div>
        <span class="cartelito">Ciencias básicas</span>
    </div>

    <div class="punto-interactivo" style="top: 9.5%; left: 34%;" onclick="abrirModalVideo('../vds_mapa/Servicios_Escolares.mp4')">
        <div class="circulo-pulso"></div>
        <span class="cartelito">Servicios escolares</span>
    </div>

    <div class="punto-interactivo" style="top: 20%; left: 30%;" onclick="abrirModalVideo('../vds_mapa/Auditorio.mp4')">
        <div class="circulo-pulso"></div>
        <span class="cartelito">Auditorio</span>
    </div>

    <div class="punto-interactivo" style="top: 85%; left: 44%;" onclick="abrirModalVideo('../vds_mapa/Maricruz.mp4')">
        <div class="circulo-pulso"></div>
        <span class="cartelito">Fab Lab</span>
    </div>

    <div class="punto-interactivo" style="top: 32%; left: 59%;" onclick="abrirModalVideo('../vds_mapa/Salon_Computo.mp4')">
        <div class="circulo-pulso"></div>
        <span class="cartelito">Oficina de Computación</span>
    </div>

</div>

<div id="modalVideo" class="modal" onclick="cerrarModalFondo(event)">
    <div class="contenido-modal">
        <span class="cerrar-modal" onclick="cerrarModalVideo()">&times;</span>
        <video id="reproductor" controls width="100%">
            <source id="videoSource" src="" type="video/mp4">
            Tu navegador no soporta la reproducción de videos.
        </video>
    </div>
</div>

<script>
    
    function abrirModalVideo(rutaVideo) {
        var modal = document.getElementById('modalVideo');
        var reproductor = document.getElementById('reproductor');
        
        if (modal && reproductor) {
            reproductor.src = rutaVideo; 
            reproductor.load();         
            modal.style.display = 'flex';
            reproductor.play();
        }
    }

    function cerrarModalVideo() {
        var modal = document.getElementById('modalVideo');
        var reproductor = document.getElementById('reproductor');
        if (modal && reproductor) {
            modal.style.display = 'none';
            reproductor.pause();
            reproductor.currentTime = 0;
        }
    }

    function cerrarModalFondo(event) {
        var modal = document.getElementById('modalVideo');
        if (event.target === modal) {
            cerrarModalVideo();
        }
    }
</script>