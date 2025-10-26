import streamlit as st
from models.modelo import Database
from difflib import get_close_matches
import pandas as pd

def buscar_medicamentos_avanzado(medicamentos, busqueda, criterio_busqueda, filtros):
    """
    Realiza una búsqueda avanzada de medicamentos según los criterios especificados.
    """
    if not medicamentos:
        return []
    
    resultados = medicamentos
    
    # Aplicar búsqueda por texto según el criterio seleccionado
    if busqueda:
        if criterio_busqueda == 'nombre':
            # Búsqueda por similitud de texto en el nombre
            nombres = [m['nombre'].lower() for m in resultados]
            coincidencias = get_close_matches(busqueda.lower(), nombres, n=len(nombres), cutoff=0.3)
            resultados = [m for m in resultados if m['nombre'].lower() in coincidencias]
        elif criterio_busqueda == 'principio_activo':
            resultados = [m for m in resultados if busqueda.lower() in str(m.get('principio_activo', '')).lower()]
        elif criterio_busqueda == 'laboratorio':
            resultados = [m for m in resultados if busqueda.lower() in str(m.get('laboratorio', '')).lower()]
    
    # Aplicar filtros
    if filtros['laboratorio'] and filtros['laboratorio'] != 'Todos':
        resultados = [m for m in resultados if m.get('laboratorio') == filtros['laboratorio']]
    
    if filtros['stock_min'] is not None:
        resultados = [m for m in resultados if m.get('stock', 0) >= filtros['stock_min']]
    
    if filtros['precio_min'] is not None:
        resultados = [m for m in resultados if m.get('precio', 0) >= filtros['precio_min']]
    
    if filtros['precio_max'] is not None:
        resultados = [m for m in resultados if m.get('precio', float('inf')) <= filtros['precio_max']]
    
    # Ordenar resultados
    if filtros['orden'] == 'nombre_asc':
        resultados.sort(key=lambda x: x.get('nombre', '').lower())
    elif filtros['orden'] == 'precio_asc':
        resultados.sort(key=lambda x: x.get('precio', 0))
    elif filtros['orden'] == 'precio_desc':
        resultados.sort(key=lambda x: x.get('precio', 0), reverse=True)
    elif filtros['orden'] == 'stock_asc':
        resultados.sort(key=lambda x: x.get('stock', 0))
    elif filtros['orden'] == 'stock_desc':
        resultados.sort(key=lambda x: x.get('stock', 0), reverse=True)
    
    return resultados

def mostrar_medicamento(med):
    """Muestra la tarjeta de un medicamento."""
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"{med['nombre']}")
            st.caption(f"**Laboratorio:** {med.get('laboratorio', 'N/A')}")
            st.write(f"**Principio Activo:** {med.get('principio_activo', 'N/A')}")
            st.write(f"**Descripción:** {med.get('descripcion', 'Sin descripción')}")
        
        with col2:
            stock = med.get('stock', 0)
            stock_min = med.get('stock_minimo', 0)
            stock_color = "red" if stock <= stock_min else "green"
            st.metric("Stock Disponible", f"{stock} unidades", 
                     delta=f"Mínimo: {stock_min}", delta_color="off")
            st.metric("Precio", f"${med.get('precio', 0):.2f}")
            
            # Mostrar alerta si el stock está por debajo del mínimo
            if stock <= stock_min:
                st.warning("¡Stock por debajo del mínimo!")

def ver_medicamentos():
    st.title("🔍 Búsqueda de Medicamentos")
    db = Database()
    
    # Obtener todos los medicamentos
    medicamentos = db.get_medicamentos()
    
    # Obtener lista de laboratorios únicos para el filtro
    laboratorios = sorted(list(set(m.get('laboratorio') for m in medicamentos if m.get('laboratorio'))))
    
# Barra lateral para filtros

    st.header("🔍 Filtros de Búsqueda")
    
    # Búsqueda principal
    busqueda = st.text_input("Término de búsqueda")
    criterio_busqueda = st.selectbox("Buscar por", 
                                    ["nombre", "principio_activo", "laboratorio"],
                                    format_func=lambda x: {"nombre": "Nombre", 
                                                        "principio_activo": "Principio Activo", 
                                                        "laboratorio": "Laboratorio"}[x])
    
    # Filtros avanzados
    with st.expander("Filtros Avanzados"):
        st.subheader("Filtros")
        
        # Filtro por laboratorio
        filtro_lab = st.selectbox(
            "Laboratorio",
            ["Todos"] + laboratorios
        )
        
        # Filtro por stock
        st.write("**Stock Mínimo:**")
        stock_min = st.number_input("Stock mínimo disponible", 
                                    min_value=0, 
                                    value=0,
                                    step=1,
                                    label_visibility="collapsed")
        
        # Filtro por rango de precios
        st.write("**Rango de Precios:**")
        col1, col2 = st.columns(2)
        with col1:
            precio_min = st.number_input("Mínimo", 
                                        min_value=0.0, 
                                        value=0.0,
                                        step=0.5,
                                        format="%.2f")
        with col2:
            precio_max = st.number_input("Máximo", 
                                        min_value=0.0, 
                                        value=1000.0,
                                        step=0.5,
                                        format="%.2f")
        
        # Ordenamiento
        st.write("**Ordenar por:**")
        orden = st.selectbox("Ordenar por",
                            ["nombre_asc", "precio_asc", "precio_desc", "stock_asc", "stock_desc"],
                            format_func={
                                "nombre_asc": "Nombre (A-Z)",
                                "precio_asc": "Precio (menor a mayor)",
                                "precio_desc": "Precio (mayor a menor)",
                                "stock_asc": "Stock (menor a mayor)",
                                "stock_desc": "Stock (mayor a menor)"
                            }.get)

    # Aplicar filtros
    filtros = {
        'laboratorio': filtro_lab if filtro_lab != "Todos" else None,
        'stock_min': stock_min if stock_min > 0 else None,
        'precio_min': precio_min if precio_min > 0 else None,
        'precio_max': precio_max if precio_max < float('inf') else None,
        'orden': orden
    }
    
    resultados = buscar_medicamentos_avanzado(medicamentos, busqueda, criterio_busqueda, filtros)
    
    # Mostrar resultados
    st.subheader(f"📋 Resultados de la búsqueda ({len(resultados)} encontrados)")
    
    if resultados:
        # Mostrar resumen de filtros aplicados
        filtros_aplicados = []
        if busqueda:
            filtros_aplicados.append(f"búsqueda: '{busqueda}' en {criterio_busqueda}")
        if filtro_lab != "Todos":
            filtros_aplicados.append(f"laboratorio: {filtro_lab}")
        if stock_min > 0:
            filtros_aplicados.append(f"stock mínimo: {stock_min}")
        if precio_min > 0 or precio_max < float('inf'):
            rango_precio = []
            if precio_min > 0:
                rango_precio.append(f"desde ${precio_min:.2f}")
            if precio_max < float('inf'):
                rango_precio.append(f"hasta ${precio_max:.2f}")
            filtros_aplicados.append("precio: " + " ".join(rango_precio))
        
        if filtros_aplicados:
            st.caption(f"Filtros aplicados: {', '.join(filtros_aplicados)}")
        
        # Mostrar resultados en pestañas
        tab1, tab2 = st.tabs(["Vista de Tarjetas", "Vista de Tabla"])
        
        with tab1:
            # Mostrar en tarjetas
            for med in resultados:
                mostrar_medicamento(med)
                
        with tab2:
            # Mostrar en tabla
            df = pd.DataFrame([{
                'Nombre': m['nombre'],
                'Laboratorio': m.get('laboratorio', 'N/A'),
                'Principio Activo': m.get('principio_activo', 'N/A'),
                'Precio': f"${m.get('precio', 0):.2f}",
                'Stock': m.get('stock', 0),
                'Stock Mínimo': m.get('stock_minimo', 0)
            } for m in resultados])
            
            # Aplicar formato condicional a la columna de stock
            def color_stock(val):
                stock = int(val.split('/')[0])
                stock_min = int(val.split('/')[1])
                color = 'red' if stock <= stock_min else 'green'
                return f'color: {color}'
            
            # Crear columna combinada para ordenar correctamente
            df['Stock_Orden'] = df.apply(lambda x: f"{x['Stock']:05d}/{x['Stock Mínimo']:05d}", axis=1)
            
            # Ordenar según el criterio seleccionado
            if orden == 'nombre_asc':
                df = df.sort_values('Nombre')
            elif orden == 'precio_asc':
                df = df.sort_values('Precio')
            elif orden == 'precio_desc':
                df = df.sort_values('Precio', ascending=False)
            elif orden == 'stock_asc':
                df = df.sort_values('Stock_Orden')
            elif orden == 'stock_desc':
                df = df.sort_values('Stock_Orden', ascending=False)
            
            # Mostrar tabla con estilo
            st.dataframe(
                df[['Nombre', 'Laboratorio', 'Principio Activo', 'Precio', 'Stock', 'Stock Mínimo']]
                .style.applymap(
                    lambda x: 'color: red' if x == 0 and isinstance(x, (int, float)) else '',
                    subset=['Stock']
                ),
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("No se encontraron medicamentos que coincidan con los criterios de búsqueda.")
        if st.button("Mostrar todos los medicamentos"):
            st.experimental_rerun()

# Para usar en la app principal:
# ver_medicamentos()
