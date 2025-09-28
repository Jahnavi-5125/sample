## Contributing

We welcome contributions! Please follow these steps:

### Development Workflow

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then clone your fork
   git clone git@github.com:IAI-solution/TheNZT_Open_Source.git
   cd TheNZT_Open_Source
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b your_name/your_feature_name
   ```

3. **Make your changes**
   - Follow existing code style and conventions
   - Add tests for new features
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Run backend tests
   uvicorn src.backend.app:app

   # Run frontend tests
   cd src/frontend
   npm run dev
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin your_name/your_feature_name
   ```

6. **Create a Pull Request**
   - Go to GitHub and create a PR from your branch
   - Provide a clear description of your changes
   - Link any related issues

### Code Style Guidelines

- **Python**: Follow PEP 8, use type hints
- **JavaScript/TypeScript**: Follow Airbnb style guide
- **Commit Messages**: Use conventional commits format
