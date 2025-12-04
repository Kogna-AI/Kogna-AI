export const growthStages = [
  {
    stage: "MVP Launch",
    range: "0-10 employees",
    description: "Initial product development and market validation",
    teamSize: 8,
    monthsToReach: 6,
    keyMilestones: [
      "First robot prototype",
      "Initial delivery tests",
      "Seed funding",
    ],
    criticalRoles: [
      {
        role: "CTO/Lead Engineer",
        count: 1,
        urgency: "critical",
        skills: ["Robotics", "AI/ML", "Systems Architecture"],
      },
      {
        role: "Robotics Engineers",
        count: 2,
        urgency: "critical",
        skills: ["ROS", "Computer Vision", "Hardware Integration"],
      },
      {
        role: "Full-Stack Developers",
        count: 2,
        urgency: "high",
        skills: ["React", "Node.js", "Mobile Development"],
      },
      {
        role: "Product Manager",
        count: 1,
        urgency: "high",
        skills: ["Product Strategy", "User Research", "Agile"],
      },
      {
        role: "Operations Lead",
        count: 1,
        urgency: "medium",
        skills: ["Logistics", "Supply Chain", "Process Design"],
      },
    ],
  },
  {
    stage: "Market Validation",
    range: "10-25 employees",
    description: "Scaling operations and refining product-market fit",
    teamSize: 20,
    monthsToReach: 12,
    keyMilestones: [
      "Series A funding",
      "100+ daily deliveries",
      "Restaurant partnerships",
    ],
    criticalRoles: [
      {
        role: "Senior ML Engineers",
        count: 2,
        urgency: "critical",
        skills: ["Machine Learning", "Computer Vision", "Path Planning"],
      },
      {
        role: "Backend Engineers",
        count: 2,
        urgency: "high",
        skills: ["Microservices", "Cloud Infrastructure", "Real-time Systems"],
      },
      {
        role: "QA Engineers",
        count: 2,
        urgency: "high",
        skills: ["Test Automation", "Robotics Testing", "Performance Testing"],
      },
      {
        role: "UX/UI Designers",
        count: 2,
        urgency: "medium",
        skills: ["Mobile Design", "User Research", "Accessibility"],
      },
      {
        role: "Business Development",
        count: 1,
        urgency: "high",
        skills: [
          "Partnership Management",
          "Restaurant Relations",
          "Negotiations",
        ],
      },
      {
        role: "Customer Support",
        count: 2,
        urgency: "medium",
        skills: ["Customer Service", "Technical Support", "Issue Resolution"],
      },
    ],
  },
  {
    stage: "Geographic Expansion",
    range: "25-75 employees",
    description: "Multi-city deployment and operational scaling",
    teamSize: 50,
    monthsToReach: 24,
    keyMilestones: [
      "Series B funding",
      "5 cities operational",
      "1000+ daily deliveries",
    ],
    criticalRoles: [
      {
        role: "Site Reliability Engineers",
        count: 3,
        urgency: "critical",
        skills: ["DevOps", "Kubernetes", "Monitoring Systems"],
      },
      {
        role: "Hardware Engineers",
        count: 3,
        urgency: "critical",
        skills: ["Embedded Systems", "Sensor Integration", "Prototyping"],
      },
      {
        role: "Regional Operations Managers",
        count: 3,
        urgency: "high",
        skills: ["Regional Management", "Team Leadership", "KPI Management"],
      },
      {
        role: "Data Scientists",
        count: 2,
        urgency: "high",
        skills: ["Analytics", "Demand Forecasting", "Route Optimization"],
      },
      {
        role: "Marketing Specialists",
        count: 3,
        urgency: "medium",
        skills: ["Digital Marketing", "Local Marketing", "Brand Management"],
      },
      {
        role: "Security Engineers",
        count: 2,
        urgency: "high",
        skills: ["Cybersecurity", "IoT Security", "Compliance"],
      },
    ],
  },
  {
    stage: "Scale & Optimization",
    range: "75-200 employees",
    description: "Market leadership and advanced AI capabilities",
    teamSize: 150,
    monthsToReach: 36,
    keyMilestones: ["Series C funding", "10+ cities", "Advanced AI routing"],
    criticalRoles: [
      {
        role: "VP of Engineering",
        count: 1,
        urgency: "critical",
        skills: [
          "Engineering Leadership",
          "Strategic Planning",
          "Team Scaling",
        ],
      },
      {
        role: "Research Scientists",
        count: 4,
        urgency: "high",
        skills: ["Advanced AI", "Autonomous Systems", "Research & Development"],
      },
      {
        role: "Platform Engineers",
        count: 5,
        urgency: "high",
        skills: ["Platform Architecture", "Scalability", "Infrastructure"],
      },
      {
        role: "Product Marketing Managers",
        count: 3,
        urgency: "medium",
        skills: ["Go-to-Market", "Competitive Analysis", "Customer Insights"],
      },
      {
        role: "Legal & Compliance",
        count: 2,
        urgency: "medium",
        skills: ["Regulatory Compliance", "Contract Law", "IP Strategy"],
      },
      {
        role: "Finance & Analytics",
        count: 3,
        urgency: "medium",
        skills: [
          "Financial Planning",
          "Business Intelligence",
          "Unit Economics",
        ],
      },
    ],
  },
];

export const objectiveHiringTriggers = {
  "Market Expansion": {
    immediateNeeds: [
      "Regional Operations Manager",
      "Business Development",
      "Marketing Specialist",
    ],
    futureNeeds: ["Data Scientist", "Customer Support"],
    urgency: "high",
  },
  "Product Innovation": {
    immediateNeeds: [
      "Senior ML Engineer",
      "Robotics Engineer",
      "Hardware Engineer",
    ],
    futureNeeds: ["Research Scientist", "UX Designer"],
    urgency: "critical",
  },
  "Operational Excellence": {
    immediateNeeds: [
      "Site Reliability Engineer",
      "QA Engineer",
      "Operations Lead",
    ],
    futureNeeds: ["Platform Engineer", "Security Engineer"],
    urgency: "high",
  },
  Technology: {
    immediateNeeds: ["Full-Stack Developer", "Backend Engineer", "ML Engineer"],
    futureNeeds: ["Research Scientist", "Platform Engineer"],
    urgency: "critical",
  },
};

export const projectionsData = [
  { month: "Jan", employees: 8, revenue: 50, deliveries: 120 },
  { month: "Mar", employees: 12, revenue: 85, deliveries: 280 },
  { month: "Jun", employees: 18, revenue: 150, deliveries: 520 },
  { month: "Sep", employees: 25, revenue: 280, deliveries: 850 },
  { month: "Dec", employees: 35, revenue: 450, deliveries: 1200 },
  { month: "Mar+1", employees: 50, revenue: 750, deliveries: 2100 },
  { month: "Jun+1", employees: 75, revenue: 1200, deliveries: 3500 },
  { month: "Dec+1", employees: 120, revenue: 2200, deliveries: 6000 },
];
