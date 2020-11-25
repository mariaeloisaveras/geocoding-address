import time, base64, geopy
import streamlit as st
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import plotly.graph_objects as go

st.title('Geocodificar endereços (Nominatim)')
st.markdown('Carregue seu arquivo CSV com o endereço (nome da rua & numero, cidade), com colunas separadas por " ; " e sem acentos ou caracteres especiais.')

def create_address_col(df):
    st.sidebar.title("Selecione a coluna de endereço")
    st.sidebar.info("Você deve selecionar a coluna de endereço (nome da rua e numero), CEP e cidade")
    nome_endereco = st.sidebar.selectbox("Selecione a coluna de ENDEREÇO", df.columns.tolist())
    numero= st.sidebar.selectbox("Selecione a coluna de NÚMERO", df.columns.tolist())
    cidade = st.sidebar.selectbox("Selecione a coluna da CIDADE", df.columns.tolist())
    pais = st.sidebar.text_input("Qual o PAÍS do endereço")
    
    df["geocode_col"] =  df[nome_endereco].astype(str) + ' ' + df[numero].astype(str) + ',' + df[cidade] + ',' + pais   
    
    return df

def choose_geocode_column(df):
    selection = st.selectbox("Selecione a coluna", df.columns.tolist())
    df['geocode_col'] = df[selection]
    
    return df

def geocode(df):
    locator = Nominatim(user_agent="myGeocoder")
    geocode = RateLimiter(locator.geocode, min_delay_seconds=1)
    df['localizacao'] = df['geocode_col'].apply(geocode)
    df['ponto'] = df['localizacao'].apply(lambda loc: tuple(loc.point) if loc else None)

    df[['latitude', 'longitude', 'altitude']] = pd.DataFrame(df['ponto'].tolist(), index=df.index)
     
    return df 

# @st.cache(persist=True, suppress_st_warning=True)
def display_map(df):
    token= "pk.eyJ1IjoibWFyaWFlbG9pc2F2ZXJhcyIsImEiOiJja2hnb2cwOGEwOWY2MnFreWp4M3p3eXNpIn0.06cjbQa4-_nMZiZxpmQXUA"

    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lat=df['latitude'],
        lon=df['longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=15,
            color='#de2d26'
        ),
        text=df['geocode_col'],
    ))
    
    fig.update_layout(
        hovermode='closest',
        mapbox=dict(
            accesstoken=token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=-23.5486,
                lon=-46.6348
            ),
            style='streets',
            pitch=0,
            zoom=10
        ),
        width=700,
        height=500,
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig


def download_csv(df):
    df_clean= df.drop(['ponto', 'localizacao','geocode_col'], axis= 1)
    csv = df_clean.to_csv(index=True, sep=';')
    b64 = base64.b64encode(csv.encode()).decode()  
    href = f'<a href="data:file/csv;base64,{b64}"> Download CSV geocodificado</a>'
    
    return href



def main():
    file = st.file_uploader("Selecione o seu arquivo")
    if file is not None:
        file.seek(0)
        df = pd.read_csv(file, low_memory=False, sep= ";")
        with st.spinner('Lendo o arquivo CSV ...'):
            time.sleep(5)
            st.success('Feito!')
        st.write(df.head())
        st.write(df.shape)



        cols = df.columns.tolist()

        st.subheader("Escolha as colunas de endereço nas barras laterais")
        st.info('Exemplo de endereço correto (em uma única coluna): "Rua Henrique Monteiro 90, Sao Paulo"')
        

        if st.checkbox("O endereço está corretamente formatado :)"):
            df_address = choose_geocode_column(df)
            st.write(df_address["geocode_col"].head())
            geocoded_df = geocode(df_address)
            with st.spinner('Aguarde, estou geocodificando...'):
                time.sleep(5)
            st.success('Feito!')
            st.write(geocoded_df.head())
            st.plotly_chart(display_map(geocoded_df))
            
            st.markdown(download_csv(geocoded_df), unsafe_allow_html=True)
        if st.checkbox("Endereço não está corretamente formatado :("):
            df_address = create_address_col(df)
            st.write(df_address["geocode_col"].head())
            geocoded_df = geocode(df_address)
            with st.spinner('Aguarde, estou geocodificando...'):
                time.sleep(5)
            st.success('Feito!')
            st.write(geocoded_df.head())
            st.plotly_chart(display_map(geocoded_df))
            st.markdown(download_csv(geocoded_df), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
