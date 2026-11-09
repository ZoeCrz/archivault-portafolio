import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <>
      {/* SECCIÓN 1: HERO PRINCIPAL DIVIDIDA */}
      <section className="split-hero landing-hero">
        
        {/* Mitad Izquierda: Textos y Botones */}
        <div className="hero-text landing-hero__copy">
          <div className="eyebrow" style={{marginBottom: '24px'}}>COLECCIONES · MARKETPLACE · COMUNIDAD</div>
          <h1 className="h-display">Objetos con un <em style={{color: 'var(--vermilion)'}}>legado</em> único.</h1>
          
          <p className="landing-hero__introduction">
            Organiza tus colecciones e inventario, publica piezas en el marketplace y comparte descubrimientos con otros coleccionistas.
          </p>
          
          <div className="landing-hero__actions">
            <Link to="/crear-cuenta" className="btn btn--sea">Crear mi bóveda &rarr;</Link>
            <a href="#beneficios" className="btn btn--ghost">Descubrir más</a>
          </div>
        </div>

        {/* Composición editorial decorativa: no representa datos ni una captura del producto. */}
        <div className="hero-image landing-hero__visual">
          <div className="landing-hero__artifact" aria-hidden="true">
            <div className="landing-hero__archive-card landing-hero__archive-card--back">
              <span>COLECCIONES</span><strong>01</strong>
            </div>
            <div className="landing-hero__archive-card landing-hero__archive-card--middle">
              <span>INVENTARIO</span><strong>02</strong>
            </div>
            <div className="landing-hero__archive-card landing-hero__archive-card--front">
              <span>COMUNIDAD</span><strong>03</strong>
            </div>
          </div>
          
          {/* Tarjeta informativa */}
          <div className="hero-floating-card landing-hero__floating-card">
            <div className="eyebrow eyebrow--ink">ÚNETE HOY</div>
            <h3 className="h-3" style={{margin: '8px 0', fontSize: '24px'}}>Comienza tu legado</h3>
            <p className="landing-hero__floating-description">
              Registra tus colecciones, documenta sus piezas y decide qué contenido quieres compartir.
            </p>
          </div>

        </div>
      </section>

      <div className="rule"></div>

      {/* SECCIÓN 2: BENEFICIOS */}
      <section id="beneficios" className="landing-benefits" aria-labelledby="beneficios-title">
        <h2 id="beneficios-title" className="landing-benefits__title">Todo tu coleccionismo en un mismo espacio</h2>
        <article className="landing-benefit">
          <div className="eyebrow" style={{ color: 'var(--sea)' }}>01 · GESTIÓN</div>
          <h3 className="h-3" style={{ margin: '16px 0', fontSize: '28px' }}>Inventario Inteligente</h3>
          <p style={{ color: 'var(--ink)', fontSize: '14px' }}>Registra piezas con sus datos, fotografías y estado de conservación, y consulta el progreso de tus colecciones.</p>
        </article>
        <article className="landing-benefit">
          <div className="eyebrow" style={{ color: 'var(--sea)' }}>02 · COMERCIO</div>
          <h3 className="h-3" style={{ margin: '16px 0', fontSize: '28px' }}>Publicaciones y ofertas</h3>
          <p style={{ color: 'var(--ink)', fontSize: '14px' }}>Publica piezas o colecciones indicando precio, condición y descripción, y gestiona las ofertas desde la aplicación.</p>
        </article>
        <article className="landing-benefit">
          <div className="eyebrow" style={{ color: 'var(--ink)' }}>03 · CONEXIÓN</div>
          <h3 className="h-3" style={{ margin: '16px 0', fontSize: '28px' }}>Comunidad Global</h3>
          <p style={{ color: 'var(--ink)', fontSize: '14px' }}>Comparte descubrimientos, comenta publicaciones, reacciona al contenido y conversa con otros usuarios.</p>
        </article>
      </section>

      <div className="rule"></div>
    </>
  );
}
