import { Link } from 'react-router-dom';

function PageSection({ section }) {
  return (
    <section id={section.id} className="information-page__section">
      <h2>{section.title}</h2>
      {section.notice && <div className="information-page__notice" role="note">{section.notice}</div>}
      {section.paragraphs?.map(paragraph => <p key={paragraph}>{paragraph}</p>)}
      {section.bullets && <ul>{section.bullets.map(item => <li key={item}>{item}</li>)}</ul>}
      {section.subsections?.map(subsection => (
        <div key={subsection.title} className="information-page__subsection">
          <h3>{subsection.title}</h3>
          {subsection.paragraphs?.map(paragraph => <p key={paragraph}>{paragraph}</p>)}
        </div>
      ))}
      {section.links?.map(link => <Link key={link.to} to={link.to} className="information-page__link">{link.label}</Link>)}
    </section>
  );
}

export default function InformationPage({ content }) {
  return (
    <article className="information-page">
      <header className="information-page__header">
        <div className="eyebrow">ARCHIVAULT · INFORMACIÓN</div>
        <h1 className="h-1">{content.title}</h1>
        <p className="information-page__introduction">{content.introduction}</p>
        {content.version && <p className="information-page__version">{content.version}</p>}
        {content.notice && <div className="information-page__notice" role="note">{content.notice}</div>}
      </header>

      <nav className="information-page__index" aria-label={`Índice de ${content.title}`}>
        <h2>En esta página</h2>
        <ul>{content.sections.map(section => <li key={section.id}><a href={`#${section.id}`}>{section.title}</a></li>)}</ul>
      </nav>

      <div className="information-page__content">
        {content.sections.map(section => <PageSection key={section.id} section={section} />)}
      </div>
    </article>
  );
}
