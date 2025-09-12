import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Breadcrumb = ({ projectName }) => {
    const location = useLocation();

    const getBreadcrumbItems = () => {
        const pathnames = location.pathname.split('/').filter(x => x);
        const items = [];

        // Always add Overview as the first item
        items.push({
            name: 'Overview',
            path: '/',
            isActive: pathnames.length === 0
        });

        // Add project name if we're on a project page
        if (pathnames[0] === 'project' && pathnames[1] && projectName) {
            items.push({
                name: projectName,
                path: `/project/${pathnames[1]}`,
                isActive: true
            });
        }

        return items;
    };

    const breadcrumbItems = getBreadcrumbItems();

    if (breadcrumbItems.length <= 1) {
        return null; // Don't show breadcrumb on overview page
    }

    return (
        <nav className="breadcrumb" aria-label="Breadcrumb">
            <ol className="breadcrumb-list">
                {breadcrumbItems.map((item, index) => (
                    <li key={item.path} className="breadcrumb-item">
                        {index < breadcrumbItems.length - 1 ? (
                            <Link to={item.path} className="breadcrumb-link">
                                {item.name}
                            </Link>
                        ) : (
                            <span className="breadcrumb-current">{item.name}</span>
                        )}
                        {index < breadcrumbItems.length - 1 && (
                            <span className="breadcrumb-separator">/</span>
                        )}
                    </li>
                ))}
            </ol>
        </nav>
    );
};

export default Breadcrumb; 