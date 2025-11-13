"""
Modelo de Machine Learning para predicción de ventas usando RandomForestRegressor.
Implementa entrenamiento, serialización y predicción de ventas futuras.
"""
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import logging

logger = logging.getLogger(__name__)

# Directorio para guardar modelos
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, 'random_forest_ventas.pkl')


class ModeloPrediccionVentas:
    """
    Clase para gestionar el modelo de predicción de ventas usando RandomForestRegressor.
    """

    def __init__(self):
        self.model = None
        self.feature_names = None
        self.is_trained = False
        self.MODEL_PATH = MODEL_PATH  # Agregar el path como atributo de instancia

        # Intentar cargar modelo existente
        self._cargar_modelo()

    def _cargar_modelo(self):
        """
        Carga un modelo entrenado si existe
        """
        try:
            if os.path.exists(self.MODEL_PATH):
                import joblib
                data = joblib.load(self.MODEL_PATH)
                self.model = data.get('model')
                self.feature_names = data.get('feature_names', [])
                self.is_trained = self.model is not None
                print(f"✅ Modelo cargado desde {self.MODEL_PATH}")
            else:
                print(f"⚠️ No se encontró modelo entrenado en {self.MODEL_PATH}")
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            self.is_trained = False

    def preparar_datos_entrenamiento(self, dias_historico=90):
        """
        Prepara los datos históricos de ventas para entrenar el modelo.
        
        Args:
            dias_historico: Número de días históricos a considerar
            
        Returns:
            DataFrame con features y target
        """
        from compra.models import Compra
        
        hoy = timezone.now().date()
        inicio = hoy - timedelta(days=dias_historico)
        
        # Obtener datos históricos diarios
        compras = Compra.objects.filter(
            fecha__date__gte=inicio
        ).values('fecha__date').annotate(
            total=Sum('total'),
            cantidad=Count('id'),
            promedio=Avg('total')
        ).order_by('fecha__date')
        
        if len(compras) < 7:
            logger.warning(f"Solo {len(compras)} días de datos. Se necesitan al menos 7 días.")
            return None
        
        # Convertir a DataFrame
        df = pd.DataFrame(list(compras))
        df['fecha'] = pd.to_datetime(df['fecha__date'])
        df = df.sort_values('fecha').reset_index(drop=True)
        
        # Crear features temporales
        df['dia_semana'] = df['fecha'].dt.dayofweek  # 0=Lunes, 6=Domingo
        df['dia_mes'] = df['fecha'].dt.day
        df['mes'] = df['fecha'].dt.month
        df['dia_anio'] = df['fecha'].dt.dayofyear
        
        # Features de ventana móvil (últimos 7 días)
        df['media_movil_7'] = df['total'].rolling(window=7, min_periods=1).mean()
        df['std_movil_7'] = df['total'].rolling(window=7, min_periods=1).std().fillna(0)
        
        # Target: total de ventas del día
        df['target'] = df['total']
        
        # Eliminar filas con NaN (solo las primeras que no tienen media móvil)
        df = df.dropna(subset=['media_movil_7']).reset_index(drop=True)
        
        if len(df) < 7:
            return None
        
        # Seleccionar features
        feature_cols = [
            'dia_semana', 'dia_mes', 'mes', 'dia_anio',
            'media_movil_7', 'std_movil_7', 'cantidad', 'promedio'
        ]
        
        X = df[feature_cols].values
        y = df['target'].values
        
        self.feature_names = feature_cols
        
        return X, y, df
    
    def entrenar(self, dias_historico=90, test_size=0.2, random_state=42):
        """
        Entrena el modelo RandomForestRegressor con datos históricos.
        
        Args:
            dias_historico: Días históricos a usar para entrenamiento
            test_size: Proporción de datos para test
            random_state: Semilla para reproducibilidad
            
        Returns:
            dict con métricas de evaluación
        """
        try:
            # Preparar datos
            resultado = self.preparar_datos_entrenamiento(dias_historico)
            if resultado is None:
                return {
                    'success': False,
                    'error': 'No hay suficientes datos históricos para entrenar'
                }
            
            X, y, df = resultado
            
            if len(X) < 10:
                return {
                    'success': False,
                    'error': f'Solo {len(X)} muestras disponibles. Se necesitan al menos 10.'
                }
            
            # Dividir en train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, shuffle=False
            )
            
            # Crear y entrenar modelo
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=random_state,
                n_jobs=-1
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluar
            y_pred_train = self.model.predict(X_train)
            y_pred_test = self.model.predict(X_test)
            
            metrics = {
                'success': True,
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'train_mae': float(mean_absolute_error(y_train, y_pred_train)),
                'test_mae': float(mean_absolute_error(y_test, y_pred_test)),
                'train_rmse': float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
                'test_rmse': float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
                'train_r2': float(r2_score(y_train, y_pred_train)),
                'test_r2': float(r2_score(y_test, y_pred_test)),
                'feature_importance': dict(zip(
                    self.feature_names,
                    self.model.feature_importances_.tolist()
                ))
            }
            
            self.is_trained = True
            
            # Guardar modelo
            self.guardar_modelo()
            
            logger.info(f"Modelo entrenado exitosamente. R² test: {metrics['test_r2']:.4f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error al entrenar modelo: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def predecir(self, dias_futuros=7, fecha_inicio=None):
        """
        Genera predicciones para los próximos días.
        
        Args:
            dias_futuros: Número de días a predecir
            fecha_inicio: Fecha desde la cual empezar (default: hoy)
            
        Returns:
            Lista de dicts con predicciones
        """
        if not self.is_trained or self.model is None:
            # Intentar cargar modelo guardado
            if not self.cargar_modelo():
                return {
                    'success': False,
                    'error': 'Modelo no entrenado. Entrena el modelo primero.'
                }
        
        try:
            from compra.models import Compra
            
            if fecha_inicio is None:
                fecha_inicio = timezone.now().date()
            
            # Obtener últimos 7 días para calcular media móvil
            inicio_hist = fecha_inicio - timedelta(days=7)
            compras_hist = Compra.objects.filter(
                fecha__date__gte=inicio_hist,
                fecha__date__lt=fecha_inicio
            ).values('fecha__date').annotate(
                total=Sum('total'),
                cantidad=Count('id'),
                promedio=Avg('total')
            ).order_by('fecha__date')
            
            # Preparar datos históricos para calcular features
            df_hist = pd.DataFrame(list(compras_hist))
            if len(df_hist) > 0:
                df_hist['fecha'] = pd.to_datetime(df_hist['fecha__date'])
                df_hist = df_hist.sort_values('fecha').reset_index(drop=True)
                media_movil = df_hist['total'].mean()
                std_movil = df_hist['total'].std() if len(df_hist) > 1 else 0
                cantidad_prom = df_hist['cantidad'].mean()
                promedio_prom = df_hist['promedio'].mean()
            else:
                # Valores por defecto si no hay historial
                media_movil = 0
                std_movil = 0
                cantidad_prom = 0
                promedio_prom = 0
            
            predicciones = []
            
            for i in range(1, dias_futuros + 1):
                fecha_pred = fecha_inicio + timedelta(days=i)
                
                # Preparar features para esta fecha
                features = np.array([[
                    fecha_pred.weekday(),  # dia_semana
                    fecha_pred.day,  # dia_mes
                    fecha_pred.month,  # mes
                    fecha_pred.timetuple().tm_yday,  # dia_anio
                    media_movil,  # media_movil_7
                    std_movil,  # std_movil_7
                    cantidad_prom,  # cantidad
                    promedio_prom  # promedio
                ]])
                
                # Predecir
                pred = self.model.predict(features)[0]
                pred = max(0, pred)  # No puede ser negativo
                
                predicciones.append({
                    'fecha': fecha_pred.isoformat(),
                    'total_predicho': round(float(pred), 2),
                    'tipo': 'prediccion'
                })
            
            return {
                'success': True,
                'predicciones': predicciones,
                'modelo': 'RandomForestRegressor',
                'fecha_entrenamiento': self.get_fecha_entrenamiento() if hasattr(self, '_fecha_entrenamiento') else None
            }
            
        except Exception as e:
            logger.error(f"Error al predecir: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def guardar_modelo(self):
        """Guarda el modelo entrenado en disco."""
        try:
            if self.model is None:
                return False
            
            modelo_data = {
                'model': self.model,
                'feature_names': self.feature_names,
                'is_trained': self.is_trained,
                'fecha_entrenamiento': timezone.now().isoformat()
            }
            
            joblib.dump(modelo_data, MODEL_PATH)
            self._fecha_entrenamiento = timezone.now()
            logger.info(f"Modelo guardado en {MODEL_PATH}")
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar modelo: {str(e)}", exc_info=True)
            return False
    
    def cargar_modelo(self):
        """Carga el modelo entrenado desde disco."""
        try:
            if not os.path.exists(MODEL_PATH):
                logger.warning(f"Modelo no encontrado en {MODEL_PATH}")
                return False
            
            modelo_data = joblib.load(MODEL_PATH)
            self.model = modelo_data['model']
            self.feature_names = modelo_data['feature_names']
            self.is_trained = modelo_data.get('is_trained', True)
            
            fecha_str = modelo_data.get('fecha_entrenamiento')
            if fecha_str:
                from django.utils.dateparse import parse_datetime
                self._fecha_entrenamiento = parse_datetime(fecha_str)
            
            logger.info(f"Modelo cargado desde {MODEL_PATH}")
            return True
            
        except Exception as e:
            logger.error(f"Error al cargar modelo: {str(e)}", exc_info=True)
            return False
    
    def get_fecha_entrenamiento(self):
        """Retorna la fecha de entrenamiento del modelo."""
        return getattr(self, '_fecha_entrenamiento', None)
    
    def esta_entrenado(self):
        """Verifica si el modelo está entrenado."""
        return self.is_trained and self.model is not None

