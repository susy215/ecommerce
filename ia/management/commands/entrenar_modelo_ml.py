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
                train_r2 = resultado.get('train_r2', 0)
                test_r2 = resultado.get('test_r2', 0)
                train_rmse = resultado.get('train_rmse', 0)
                test_rmse = resultado.get('test_rmse', 0)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Modelo entrenado exitosamente!\n'
                        f'📊 Datos usados: {resultado.get("train_samples", 0)} train, {resultado.get("test_samples", 0)} test\n'
                        f'📈 Train R²: {train_r2:.3f}, Test R²: {test_r2:.3f}\n'
                        f'📊 Train RMSE: {train_rmse:.2f}, Test RMSE: {test_rmse:.2f}\n'
                        f'💾 Modelo guardado en: {modelo.MODEL_PATH}'
                    )
                )

                # Mostrar importancia de features
                feature_importance = resultado.get('feature_importance', {})
                if feature_importance:
                    self.stdout.write('🔍 Importancia de Features:')
                    for feature, importance in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True):
                        self.stdout.write(f'   {feature}: {importance:.3f}')
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
