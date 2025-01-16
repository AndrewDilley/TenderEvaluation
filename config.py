import os

# Determine DOCUMENTS_PATH based on the environment

if os.getenv("DOCKER_ENV") == "true":
    DOCUMENTS_PATH = "/app/documents"
    PREPROCESSED_PATH = "/app/preprocessed_data"
else:
    DOCUMENTS_PATH = "C:/Users/andrew.dilley/development/chatbot12/documents"
    PREPROCESSED_PATH = "C:/Users/andrew.dilley/development/chatbot12/preprocessed_data"



SHAREPOINT_LINKS = {
    "Alcohol and Drugs in the Workplace Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/508",
    "Consequence Of Employee Misconduct.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/286",
    "Contractor Management Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/417",
    "Cyber Security Incident Response Plan Framework.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/885",
    "Flexible Working Arrangements Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/640",
    "Gifts Benefits and Hospitality Policy - BOARD.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/822",
    "Hazard Reporting Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/293",
    "Incident Reporting and Response Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/665",
    "Information Technology Security Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/815",
    "Mobile Phone Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/896",
    "Motor Vehicle Operational Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/240",
    "Personal Protective Equipment and Field Uniform.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/230",
    "Vehicle Logbook Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1321",
    "Physical Security Policy.docx": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1355",
    "Use of text based Generative Artificial Intelligence (AI).DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1373",
    "Vehicle Safety System Alarm Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/883",
    "Vehicle Safety System Manual.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1317",
    "Wannon Water Enterprise Agreement 2020.PDF": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/908",
    "Bullying, Discrimination & Harassment Free Workplace Procedure.docx": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1438",
    "Customer Support Policy.docx": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1090",
    "Cyber Resilience Policy.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/881",
    "Zero Harm Policy.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/722",
    "Access Control Policy.docx": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1151",
    "Corporate Catering Procedure.docx": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1420",
    "Digital Change Procedure.docx": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1257",
    "Document Control Procedure.docx": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/907",
    "Email Usage Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/201",
    "Employee Departures Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1439",
    "Employee Gift Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/835",
    "Expenditure Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/367",
    "Family and Domestic Violence Guidelines - Managers and Leaders.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/383",
    "Family and Domestic Violence Procedure - Employees.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1370",
    "Higher Duties Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/481",
    "Internet Usage Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/176",
    "Learning and Development Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/368",
    "Media and Social Media Management Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/727",
    "Occupational Rehabilitation Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1541",
    "Our Voice Guide - January 2023.pdf": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1216",
    "Physical Access Control Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1507",
    "Procurement Policy.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/799",
    "Records Management Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/413",
    "Risk Management Plan.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/690",
    "Smoke free Workplace Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/258",
    "Tertiary Study Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/573",
    "Urban Water Strategy 2022.pdf": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1417",
    "Wannon Water Dress Code and Logoed Clothing Procedure.DOCX": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/182",
    "Wannon Water Health and Safety Representatives.docx.pdf": "https://wannonwater.sharepoint.com/sites/cdms/SitePages/Homepage.aspx#/PublishedDocumentView/1401"


    # Add other files here
}
