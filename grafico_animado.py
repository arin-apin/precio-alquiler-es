import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Leer los datos del CSV
df = pd.read_csv('/home/pablo/Downloads/alquileres.csv')

# Convertir la columna 'Mes' en índice
df.set_index('Mes', inplace=True)

# Convertir todas las columnas de temperatura a flotantes
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Ordenar el índice para tener los datos más antiguos primero
df.sort_index(ascending=True, inplace=True)
print(df)

# Preparar la figura y los ejes para la animación
fig, ax = plt.subplots()

def animate(i):
    ax.clear()
    # Seleccionar la fila de datos para el mes actual
    data = df.iloc[i]
    # Ordenar los valores de mayor a menor
    data_sorted = data.sort_values(ascending=False)
    print(data_sorted)
    # Crear las barras
    bars = ax.bar(data_sorted.index, data_sorted.values, color='royalblue')
    # Añadir etiquetas y título
    ax.set_xlabel('Ciudades')
    ax.set_ylabel('Precio')
    ax.set_title(f'Precio del alquiler en €/m2 en {df.index[i]}')

# Configurar la animación
ani = animation.FuncAnimation(fig, animate, frames=len(df), interval=200, repeat=False)

# Mostrar el gráfico
plt.show()
# Salvar animación
# ani.save('alquileres.gif', writer='imagemagick')
