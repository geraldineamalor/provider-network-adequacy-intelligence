# Provider Network Adequacy Intelligence - Frontend

A React-based frontend application for analyzing provider network adequacy and generating AI-powered recruitment recommendations.

## 🚀 Features

- **Modern Facebook-style UI**: Clean, intuitive interface with responsive design
- **Interactive Geographic Selection**: Select states and counties for analysis
- **Specialty Filtering**: Choose medical specialties with search and category filters
- **Real-time Analysis**: Animated progress tracking during analysis
- **Interactive Map Visualization**: View access gaps on an interactive map using Leaflet
- **Comprehensive Results**: Detailed gap analysis with scores, metrics, and explanations
- **AI-Powered Recommendations**: Prioritized provider recruitment suggestions
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## 📋 Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)

## 🛠️ Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## 🏃 Running the Application

### Development Mode

Start the development server:
```bash
npm start
```

The application will open in your browser at [http://localhost:3000](http://localhost:3000)

### Production Build

Create an optimized production build:
```bash
npm run build
```

The build files will be in the `build/` directory.

## 🗂️ Project Structure

```
frontend/
├── public/                 # Static files
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── Badge.jsx
│   │   ├── Button.jsx
│   │   ├── Card.jsx
│   │   ├── EmptyState.jsx
│   │   ├── ErrorMessage.jsx
│   │   ├── LoadingSpinner.jsx
│   │   ├── MapView.jsx
│   │   ├── Modal.jsx
│   │   └── SearchBox.jsx
│   ├── layouts/           # Layout components
│   │   ├── MainLayout.jsx
│   │   └── MainLayout.css
│   ├── pages/             # Page components
│   │   ├── Dashboard.jsx
│   │   ├── SelectArea.jsx
│   │   ├── SelectSpecialty.jsx
│   │   ├── Analysis.jsx
│   │   ├── Results.jsx
│   │   └── Recommendations.jsx
│   ├── services/          # API services
│   │   └── api.js
│   ├── App.jsx            # Main app component
│   ├── App.css
│   ├── index.js           # Entry point
│   └── index.css          # Global styles
└── package.json
```

## 🎨 Design System

### Color Palette

- **Primary Blue**: #1877f2 (Facebook-inspired)
- **Secondary Green**: #42b72a
- **Background**: #f0f2f5
- **Surface**: #ffffff
- **Border**: #dddfe2

### Status Colors

- **Critical**: #dc3545
- **High**: #fd7e14
- **Medium**: #ffc107
- **Low**: #28a745
- **Info**: #17a2b8

## 🔗 API Integration

The application uses a service layer (`src/services/api.js`) to communicate with the backend.

### Mock Data Mode

By default, the app runs with mock data. To connect to a real backend:

1. Update `src/services/api.js`:
```javascript
const USE_MOCK_DATA = false; // Change to false
const API_BASE_URL = 'http://your-backend-url/api';
```

2. Ensure backend API endpoints match the expected contract:
- `GET /areas` - Get all states/geographic areas
- `GET /areas/:stateCode/counties` - Get counties for a state
- `GET /specialties` - Get all medical specialties
- `GET /providers` - Get providers (with optional filters)
- `POST /analysis` - Submit analysis request
- `GET /analysis/:id` - Get analysis results
- `GET /recommendations` - Get recommendations

## 🧭 User Journey

1. **Dashboard** (`/`) - Landing page with overview and quick actions
2. **Select Area** (`/select-area`) - Choose state and counties
3. **Select Specialty** (`/select-specialty`) - Choose medical specialties
4. **Analysis** (`/analysis`) - Real-time analysis with progress tracking
5. **Results** (`/results`) - View gap analysis with map and list views
6. **Recommendations** (`/recommendations`) - AI-powered recruitment recommendations

## 📦 Dependencies

### Core
- `react` - UI library
- `react-dom` - React DOM renderer
- `react-router-dom` - Routing

### Data & API
- `axios` - HTTP client for API calls

### Mapping
- `leaflet` - Interactive maps
- `react-leaflet` - React wrapper for Leaflet

### Visualization
- `recharts` - Chart library (installed but available for future use)

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```
REACT_APP_API_URL=http://localhost:8000/api
```

## 🧪 Testing

Run tests:
```bash
npm test
```

## 🚢 Deployment

### Build for Production

```bash
npm run build
```

### Deploy to Static Hosting

The `build/` folder can be deployed to:
- Netlify
- Vercel
- AWS S3 + CloudFront
- Azure Static Web Apps
- GitHub Pages

## 🎯 Key Features Explained

### Interactive Components

All buttons, cards, and interactive elements provide visual feedback:
- Hover effects
- Click animations
- Loading states
- Error handling

### Responsive Design

- Mobile-first approach
- Breakpoints at 768px and 1024px
- Flexible grids and layouts
- Touch-friendly interactions

### State Management

- React hooks (useState, useEffect)
- Session storage for cross-page data
- No external state management needed for MVP

## 🐛 Troubleshooting

### Map Not Displaying

If the Leaflet map doesn't display:
1. Ensure `leaflet` CSS is imported
2. Check browser console for errors
3. Verify marker icon paths

### API Connection Issues

1. Check `USE_MOCK_DATA` flag in `api.js`
2. Verify backend URL in environment variables
3. Check CORS settings on backend
4. Inspect network tab in browser DevTools

## 📝 Code Style

- ES6+ JavaScript
- Functional components with hooks
- CSS modules or scoped CSS
- Consistent naming conventions
- Comments for complex logic

## 🤝 Integration with Backend

### Expected API Response Formats

**Areas:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "California",
      "code": "CA",
      "counties": 58
    }
  ]
}
```

**Analysis Results:**
```json
{
  "data": {
    "summary": {
      "totalProviders": 1247,
      "averageDistance": 8.3,
      "accessGapScore": 67,
      "criticalAreas": 5
    },
    "gapAreas": [...],
    "recommendations": [...]
  }
}
```

## 📄 License

This project is part of an AI/ML hackathon.

## 👥 Team

- **FE-1**: Core Frontend Developer (this application)
- **FE-2**: UI/Map Components Developer
- **BE-1**: Backend API Developer
- **BE-2**: Database Developer
- **BE-3**: Geospatial Services Developer
- **ML-3**: ML Model Developer

## 📞 Support

For issues or questions, contact the Team Lead or open an issue in the project repository.

---

**Built with ❤️ for the Provider Network Adequacy Intelligence Project**
