import { useState, useEffect, useReducer, useRef } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import MediaImage from '../../components/MediaImage';
import MarketplacePublicationForm from '../../components/MarketplacePublicationForm';
import { apiRequest } from '../../services/api';
import { notifyApiError } from '../../services/errors';
import {
  createMarketplacePublication,
  createSaleFormState,
  hasSaleErrors,
  saleFieldErrorsFrom,
  saleFormReducer,
  validateSaleData,
} from '../../services/publications';

const Icons = {
  Image: () => <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>,
  X: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
};

export default function NuevaPieza() {
  const navigate = useNavigate();
  const { addNotification } = useOutletContext() || { addNotification: () => {} };
  
  const [formData, setFormData] = useState({
    nombre: '', categoria: '', descripcion: '', coleccionSeleccionada: '', 
    nombreColeccionNueva: '', categoriaColeccionNueva: '', tipoColeccionNueva: 'personal', piezasTotalesNueva: '',
    enVenta: false,
  });
  const [saleForm, dispatchSaleForm] = useReducer(
    saleFormReducer,
    'NUEVA',
    createSaleFormState,
  );
  
  const [colecciones, setColecciones] = useState([]);
  const [loading, setLoading] = useState(false);
  const [imagenArchivo, setImagenArchivo] = useState(null);
  const [imgPreview, setImgPreview] = useState(null);
  const [imgColArchivo, setImgColArchivo] = useState(null);
  const [imgColPreview, setImgColPreview] = useState(null);
  const submitInFlightRef = useRef(false);

  const API_URL = import.meta.env.VITE_API_URL;
  const userId = parseInt(localStorage.getItem('archivault_user_id'), 10);

  useEffect(() => {
    const fetchColecciones = async () => {
      if (isNaN(userId)) return;
      try {
        const [dataUsu, dataMae] = await Promise.all([
            apiRequest(`${API_URL}/api/v1/catalog/colecciones-usuario/`),
            apiRequest(`${API_URL}/api/v1/catalog/colecciones/`)
        ]);
        const listaUsu = Array.isArray(dataUsu) ? dataUsu : (dataUsu.results || []);
        const listaMae = Array.isArray(dataMae) ? dataMae : (dataMae.results || []);
        const nombresMaestras = {};
        listaMae.forEach(m => { nombresMaestras[m.id] = m.nombre; });

        const misColecciones = listaUsu.filter(c => c.user === userId).map(c => {
            const maestraId = c.coleccion || c.coleccion_id;
            return { ...c, nombreMostrado: nombresMaestras[maestraId] || `Colección #${c.id}` };
        });
        setColecciones(misColecciones);
      } catch (error) { notifyApiError(addNotification, error, 'No se pudieron cargar tus colecciones'); }
    };
    fetchColecciones();
  }, [userId, API_URL, addNotification]);

  const handleChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({ ...formData, [e.target.name]: value });
  };

  const handleImageUpload = (e) => {
      if(e.target.files && e.target.files[0]) {
          setImagenArchivo(e.target.files[0]);
          setImgPreview(URL.createObjectURL(e.target.files[0]));
      }
  };

  const handleColImageUpload = (e) => {
      if(e.target.files && e.target.files[0]) {
          setImgColArchivo(e.target.files[0]);
          setImgColPreview(URL.createObjectURL(e.target.files[0]));
      }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading || submitInFlightRef.current) return;
    if (formData.enVenta) {
      const validationErrors = validateSaleData(saleForm.data);
      if (hasSaleErrors(validationErrors)) {
        dispatchSaleForm({ type: 'errors', errors: validationErrors });
        return;
      }
      dispatchSaleForm({ type: 'submit' });
    }
    submitInFlightRef.current = true;
    setLoading(true);

    try {
      let coleccionUsuarioId = null;
      let colMaestraInyectar = 1;
      
      if (formData.coleccionSeleccionada === 'NEW') {
          const payloadCol = new FormData();
          payloadCol.append('nombre', formData.nombreColeccionNueva);
          payloadCol.append('categoria', formData.categoriaColeccionNueva || 'General');
          payloadCol.append('tipo', formData.tipoColeccionNueva);
          if (imgColArchivo) payloadCol.append('imagen', imgColArchivo);
          payloadCol.append('total_piezas', formData.tipoColeccionNueva === 'global' ? (formData.piezasTotalesNueva || 0) : 0);
          if (formData.tipoColeccionNueva === 'personal') {
              payloadCol.append('propietario', userId);
          }
          
          const dataMaestra = await apiRequest(`${API_URL}/api/v1/catalog/colecciones/`, { method: 'POST', body: payloadCol });

          const dataUsuCol = await apiRequest(`${API_URL}/api/v1/catalog/colecciones-usuario/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ coleccion: dataMaestra.id, user: userId }) });
          coleccionUsuarioId = dataUsuCol.id;
          colMaestraInyectar = dataMaestra.id;
      } else { 
          coleccionUsuarioId = parseInt(formData.coleccionSeleccionada, 10);
          const colActual = colecciones.find(c => c.id === coleccionUsuarioId);
          if(colActual) colMaestraInyectar = colActual.coleccion || colActual.coleccion_id || 1;
      }

      let catalogoId = null;
      let listaCats = await apiRequest(`${API_URL}/api/v1/catalog/piezas-catalogo/`);
      listaCats = Array.isArray(listaCats) ? listaCats : (listaCats.results || []);
      const catExistente = listaCats.find(c => c.nombre && c.nombre.toLowerCase() === formData.nombre.toLowerCase() && c.coleccion === colMaestraInyectar);

      if (catExistente) { catalogoId = catExistente.id; } else {
          const newCat = await apiRequest(`${API_URL}/api/v1/catalog/piezas-catalogo/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nombre: formData.nombre, numero_item: "1", sku_base: formData.descripcion, coleccion: colMaestraInyectar }) });
          catalogoId = newCat.id;
      }

      const payloadInventario = new FormData();
      payloadInventario.append('nombre_personalizado', formData.nombre);
      payloadInventario.append('sku', formData.descripcion);
      payloadInventario.append('estado_adquisicion', 'ADQUIRIDA');
      payloadInventario.append('visibilidad', formData.enVenta ? 'PUBLICA' : 'PRIVADA');
      payloadInventario.append('condicion', saleForm.data.condicion || 'NUEVA');
      payloadInventario.append('coleccion_usuario', coleccionUsuarioId);
      payloadInventario.append('pieza_catalogo', catalogoId);
      payloadInventario.append('user', userId);

      const dataInv = await apiRequest(`${API_URL}/api/v1/catalog/inventario/`, { method: 'POST', body: payloadInventario });

      if (imagenArchivo) {
          const payloadFoto = new FormData();
          payloadFoto.append('pieza_inventario', dataInv.id);
          payloadFoto.append('archivo', imagenArchivo);
          await apiRequest(`${API_URL}/api/v1/catalog/fotos/`, { method: 'POST', body: payloadFoto });
      }

      if (formData.enVenta) {
          await createMarketplacePublication(API_URL, {
            targetType: 'piece',
            targetId: dataInv.id,
            data: saleForm.data,
          });
      }

      addNotification("Pieza Creada", `El artículo ha sido documentado en la bóveda.`, "success");
      dispatchSaleForm({ type: 'success', initialCondition: 'NUEVA' });
      navigate('/app/colecciones');

    } catch (error) {
        const fieldErrors = saleFieldErrorsFrom(error);
        if (formData.enVenta && hasSaleErrors(fieldErrors)) {
          dispatchSaleForm({ type: 'errors', errors: fieldErrors });
        } else {
          notifyApiError(addNotification, error, 'No se pudo registrar la pieza');
        }
    } finally {
      submitInFlightRef.current = false;
      setLoading(false);
      dispatchSaleForm({ type: 'settled' });
    }
  };

  return (
    <div className="view-container layout-container new-piece-page">
      <div className="new-piece-page__content">
        <div className="eyebrow" style={{marginBottom: '16px'}}>NUEVO REGISTRO AVANZADO</div>
        <h1 className="h-2" style={{marginBottom: '40px'}}>Registrar Pieza</h1>

        <form className="new-piece-form" onSubmit={handleSubmit}>
          
          <div className="form-group" style={{marginBottom: '40px'}}>
            <label className="eyebrow" style={{display: 'block', marginBottom: '12px'}}>COLECCIÓN A LA QUE PERTENECE</label>
            <select name="coleccionSeleccionada" className="editorial-input" value={formData.coleccionSeleccionada} onChange={handleChange} required style={{ cursor: 'pointer', appearance: 'auto', fontSize: '20px' }}>
              <option value="" disabled>-- Selecciona el álbum o colección --</option>
              {colecciones.map(col => (<option key={col.id} value={col.id}>{col.nombreMostrado}</option>))}
              <option value="NEW" style={{fontWeight: 'bold', color: 'var(--vermilion)'}}>+ Crear nueva bóveda/colección...</option>
            </select>
            
            {formData.coleccionSeleccionada === 'NEW' && (
              <div className="new-piece-form__new-collection">
                <div className="new-piece-form__collection-cover">
                  <div className="eyebrow" style={{marginBottom: '12px'}}>PORTADA ÁLBUM</div>
                  {!imgColPreview ? (
                      <label style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '16px', border: '2px dashed var(--ink-20)', borderRadius: '8px', cursor: 'pointer', color: 'var(--ink-60)', height: '140px', textAlign: 'center'}}>
                          <span style={{fontWeight: 'bold', color: 'var(--sea)', fontSize: '12px'}}>Añadir Portada</span>
                          <input type="file" style={{display: 'none'}} accept="image/*" onChange={handleColImageUpload} />
                      </label>
                  ) : (
                      <div style={{position: 'relative', borderRadius: '8px', overflow: 'hidden', height: '140px'}}>
                          <MediaImage sources={imgColPreview} alt="Vista previa de la colección" style={{width: '100%', height: '100%', objectFit: 'cover'}} />
                          <button type="button" className="collection-media-remove collection-media-remove--compact" aria-label="Retirar portada de la colección" onClick={() => {setImgColPreview(null); setImgColArchivo(null);}}><Icons.X /></button>
                      </div>
                  )}
                </div>

                <div style={{flex: 1}}>
                  <div className="eyebrow" style={{marginBottom: '16px', color: 'var(--sea)'}}>DATOS DE LA NUEVA COLECCIÓN</div>
                  <input type="text" name="nombreColeccionNueva" className="editorial-input" placeholder="Nombre de la colección (Ej. Álbum Panini)" value={formData.nombreColeccionNueva} onChange={handleChange} required autoFocus style={{marginBottom: '24px', padding: '8px 0', fontSize: '18px'}} />
                  <input type="text" name="categoriaColeccionNueva" className="editorial-input" placeholder="Categoría de Colección (Ej. TCG, Deportes)" value={formData.categoriaColeccionNueva} onChange={handleChange} required style={{marginBottom: '24px', padding: '8px 0', fontSize: '16px'}} />
                  
                  <div className={`new-piece-form__fields ${formData.tipoColeccionNueva === 'global' ? 'new-piece-form__fields--split' : ''}`}>
                      <div>
                          <label className="eyebrow" style={{display: 'block', marginBottom: '8px'}}>TIPO DE COLECCIÓN</label>
                          <select name="tipoColeccionNueva" className="editorial-input" value={formData.tipoColeccionNueva} onChange={handleChange} style={{appearance: 'auto', fontSize: '14px', padding: '8px 0'}}>
                              <option value="personal">Personal (Infinita)</option>
                              <option value="global">Oficial Global (Cerrada)</option>
                          </select>
                      </div>
                      {formData.tipoColeccionNueva === 'global' && (
                          <div>
                              <label className="eyebrow" style={{display: 'block', marginBottom: '8px'}}>PIEZAS TOTALES</label>
                              <input type="number" name="piezasTotalesNueva" className="editorial-input" placeholder="Ej. 638" value={formData.piezasTotalesNueva} onChange={handleChange} style={{fontSize: '14px', padding: '8px 0'}} required />
                          </div>
                      )}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="form-group" style={{marginBottom: '48px'}}>
              <label className="eyebrow" style={{display: 'block', marginBottom: '16px'}}>FOTOGRAFÍA OFICIAL DE LA PIEZA (OPCIONAL)</label>
              {!imgPreview ? (
                  <label className="new-piece-form__upload">
                      <Icons.Image />
                      <span style={{fontWeight: 'bold', color: 'var(--sea)', marginTop: '16px', fontSize: '18px'}}>Adjuntar Fotografía Real</span>
                      <input type="file" style={{display: 'none'}} accept="image/*" onChange={handleImageUpload} />
                  </label>
              ) : (
                  <div className="new-piece-form__preview">
                      <MediaImage sources={imgPreview} alt="Vista previa de la pieza" className="new-piece-form__preview-image" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      <button type="button" className="new-piece-form__remove-media" aria-label="Retirar fotografía de la pieza" onClick={() => {setImgPreview(null); setImagenArchivo(null);}}><Icons.X /></button>
                  </div>
              )}
          </div>

          <div className="form-group" style={{marginBottom: '40px'}}>
            <label className="eyebrow" style={{display: 'block', marginBottom: '12px'}}>NOMBRE DE LA PIEZA</label>
            <input type="text" name="nombre" className="editorial-input" placeholder="Ej. Tarjeta Holográfica Edición Especial" value={formData.nombre} onChange={handleChange} required style={{fontSize: '24px'}} />
          </div>

          <div className="new-piece-form__fields new-piece-form__fields--split new-piece-form__fields--spaced">
            <div className="form-group">
              <label className="eyebrow" style={{display: 'block', marginBottom: '12px'}}>CATEGORÍA DE LA PIEZA</label>
              <input type="text" name="categoria" className="editorial-input" placeholder="Ej. Tarjeta, Calzado, Accesorio..." value={formData.categoria} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label className="eyebrow" style={{display: 'block', marginBottom: '12px'}}>SKU / CERTIFICADO</label>
              <input type="text" name="descripcion" className="editorial-input" placeholder="Ej. CERT-98234" value={formData.descripcion} onChange={handleChange} required />
            </div>
          </div>

          <div className="rule" style={{marginBottom: '48px'}}></div>

          <div className="new-piece-form__sale">
              <label className="new-piece-form__sale-toggle">
                  <input type="checkbox" name="enVenta" checked={formData.enVenta} onChange={handleChange} style={{width: '24px', height: '24px', accentColor: 'var(--vermilion)'}} />
                  Ofrecer pieza en el Marketplace
              </label>
              {formData.enVenta && (
                  <div style={{marginTop: '40px'}}>
                    <MarketplacePublicationForm
                      value={saleForm.data}
                      onChange={(field, value) => dispatchSaleForm({ type: 'change', field, value })}
                      fieldErrors={saleForm.fieldErrors}
                      submitting={loading || saleForm.submitting}
                      showActions={false}
                    />
                  </div>
              )}
          </div>

          <div className="new-piece-form__actions">
            <button type="button" className="btn btn--outline" onClick={() => navigate('/app/colecciones')} style={{padding: '16px 32px'}}>Cancelar</button>
            <button type="submit" className="btn btn--vermilion" disabled={loading} style={{padding: '16px 48px', fontSize: '16px'}}>
              {loading ? 'Sincronizando Base de Datos...' : 'Guardar y Finalizar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
