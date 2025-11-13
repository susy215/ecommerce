"""
Comando para entrenar el modelo de Machine Learning de predicción de ventas.
"""
from django.core.management.base import BaseCommand
from ia.modelo_ml import ModeloPrediccionVentas


class Command(BaseCommand):
    help = 'Entrena el modelo de Machine Learning para predicción de ventas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias-historico',
            type=int,
            default=90,
            help='Número de días históricos para entrenar (default: 90)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar reentrenamiento incluso si ya existe un modelo'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando entrenamiento del modelo ML...')
        )

        # Verificar si ya existe un modelo
        modelo = ModeloPrediccionVentas()

        if modelo.is_trained and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️ Ya existe un modelo entrenado. '
                    f'Usa --force para reentrenar.'
                )
            )
            return

        # Preparar datos de entrenamiento
        self.stdout.write('📊 Preparando datos de entrenamiento...')
        try:
            df = modelo.preparar_datos_entrenamiento(
                dias_historico=options['dias_historico']
            )
            self.stdout.write(
                f'✅ Datos preparados: {len(df)} registros históricos'
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error preparando datos: {e}')
            )
            return

        # Verificar que hay suficientes datos
        if len(df) < 3:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Insuficientes datos para entrenar. '
                    f'Solo {len(df)} registros. Necesitas al menos 3.'
                )
            )
            return

        # Entrenar modelo
        self.stdout.write('🤖 Entrenando modelo RandomForestRegressor...')
        try:
            resultado = modelo.entrenar(df)
            if resultado.get('success'):
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Modelo entrenado exitosamente!\n'
                        f'📈 Precisión (R²): {resultado.get("r2_score", "N/A"):.3f}\n'
                        f'📊 RMSE: {resultado.get("rmse", "N/A"):.2f}\n'
                        f'💾 Modelo guardado en: {modelo.MODEL_PATH}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Error entrenando modelo: {resultado.get("error", "Error desconocido")}'
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante entrenamiento: {e}')
            )

        self.stdout.write(
            self.style.SUCCESS('🎉 Proceso de entrenamiento completado!')
        )
